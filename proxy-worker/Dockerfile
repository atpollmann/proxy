FROM tiangolo/uvicorn-gunicorn-starlette:python3.9

COPY . /app
WORKDIR /app

RUN apt-get update
RUN pip3 install --upgrade pip --no-cache-dir -r requirements.txt
