FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

COPY ./control-api-rest /app

WORKDIR /app

RUN apt-get update
RUN pip3 install --upgrade pip --no-cache-dir -r requirements.txt
