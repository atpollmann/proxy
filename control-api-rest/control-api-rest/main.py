from fastapi import FastAPI, Body, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
from config import HOST_CONTROL_DB
from pydantic import BaseModel, Field, IPvAnyNetwork
from typing import List, Optional
import motor.motor_asyncio

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient(
    f"mongodb://{HOST_CONTROL_DB}:27017/proxy_db")
db = client.proxy_db


class PyObjectId(ObjectId):
    """
    ObjectId can't be directly encoded as JSON
    @Credit: https://github.com/mongodb-developer/mongodb-with-fastapi/blob/master/app.py
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class RuleModel(BaseModel):
    type = "rule"
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    ip: IPvAnyNetwork = Field(...)
    path: str = Field(...)
    rate: int = Field(..., ge=0)
    unit: str = Field(..., max_length=1, regex="s|m")

    class Config:
        json_encoders = {ObjectId: str}


class UpdateRuleModel(BaseModel):
    ip: Optional[IPvAnyNetwork]
    path: Optional[str]
    rate: Optional[int]
    unit: Optional[str]

    class Config:
        json_encoders = {ObjectId: str}


@app.post("/rules", response_description="Add new rule", response_model=RuleModel)
async def create_rule(rule: RuleModel = Body(...)):
    student = jsonable_encoder(rule)
    new_rule = await db["access_list"].insert_one(student)
    created_rule = await db["access_list"].find_one({"_id": new_rule.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_rule)


@app.get("/rules", response_description="List rules", response_model=List[RuleModel])
async def list_rules():
    rules = await db["access_list"].find({"type": "rule"}).to_list(1000)
    return rules


@app.get("/rules/{rule_id}", response_description="Get a single rule", response_model=RuleModel)
async def show_rule(rule_id: str):
    if (rule := await db["access_list"].find_one({"_id": rule_id})) is not None:
        return rule

    raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")


@app.put("/rules/{rule_id}", response_description="Update a rule", response_model=RuleModel)
async def update_rule(rule_id: str, rule: UpdateRuleModel = Body(...)):
    rule = {k: v for k, v in rule.dict().items() if v is not None}

    if len(rule) >= 1:
        update_result = await db["access_list"].update_one({"_id": rule_id}, {"$set": rule})

        if update_result.modified_count == 1:
            if (updated_rule := await db["access_list"].find_one({"_id": rule_id})) is not None:
                return updated_rule

    if (existing_rule := await db["access_list"].find_one({"_id": rule_id})) is not None:
        return existing_rule

    raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")


@app.delete("/rules/{rule_id}", response_description="Delete a rule")
async def delete_rule(rule_id: str):
    delete_result = await db["access_list"].delete_one({"_id": rule_id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
