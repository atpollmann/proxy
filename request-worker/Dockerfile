FROM tiangolo/uvicorn-gunicorn-starlette:python3.9

COPY ./request-worker /app
WORKDIR /app

RUN apt-get update
RUN pip3 install --upgrade pip --no-cache-dir -r requirements.txt
RUN apt-get install -y redis-server
