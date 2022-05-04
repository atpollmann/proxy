import pika
import sys
import os
import json

from pymongo import MongoClient
from config import HOST_ANALYTICS_DB, HOST_BROKER, EXCHANGE_NAME

mongoClient = MongoClient(HOST_ANALYTICS_DB)
proxy_db = mongoClient.proxy_db
requests = proxy_db.requests


def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=HOST_BROKER))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name)

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    channel.start_consuming()


def callback(ch, method, properties, body):
    request = json.loads(body)
    requests.insert_one(request)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
