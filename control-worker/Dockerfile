FROM python:3.9

COPY ./control-worker /app

WORKDIR /app

RUN pip3 install --upgrade pip --no-cache-dir -r requirements.txt

CMD ["bash", "prestart.sh"]
