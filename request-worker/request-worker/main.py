import redis
import httpx
import pika
import json

from datetime import datetime
from starlette.requests import Request
from starlette.responses import Response
from endpoint import endpoint
from config import EXCHANGE_NAME, HOST_BROKER

DESTINATION_ENDPOINT: str = endpoint
redisClient = redis.Redis()


async def app(scope, receive, send):
    request = Request(scope, receive)

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST_BROKER))
    channel = connection.channel()

    hit = redisClient.get(f"{request.client.host}{request.url.path}")
    redisClient.close()

    if hit:
        print("Found hit in local storage. Access denied")
        response = Response(status_code=429)
    else:
        url = DESTINATION_ENDPOINT + request.url.path
        content = httpx.get(url)
        response = Response(content.text, media_type="application/json")

    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout')
    date = datetime.now()
    message = {
        'datetime': date.isoformat(),
        'ip': request.client.host,
        'path': request.url.path,
        'method': request.method,
        'allow': hit is None
    }

    channel.basic_publish(exchange=EXCHANGE_NAME, routing_key='', body=json.dumps(message))
    print("REQUEST WORKER: message send to exchange")
    print(json.dumps(message))
    connection.close()

    await response(scope, receive, send)
