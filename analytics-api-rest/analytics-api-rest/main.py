from fastapi import FastAPI
from bson import ObjectId
from config import HOST_ANALYTICS_DB
from pydantic import BaseModel, Field, IPvAnyNetwork
from typing import List
import motor.motor_asyncio

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient(
    f"mongodb://{HOST_ANALYTICS_DB}:27017/proxy_db")
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


class RequestModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    datetime: str = Field(...)
    ip: str = Field(...)
    path: str = Field(...)
    method: str = Field(...)
    allow: bool = Field(...)

    class Config:
        json_encoders = {ObjectId: str}


@app.get("/requests", response_description="List requests", response_model=List[RequestModel])
async def list_requests():
    requests = await db["requests"].find().to_list(1000)
    return requests
