import redis
import pika
import sys
import os

from pymongo import MongoClient
from config import HOST_CONTROL_DB, HOST_CACHE_MASTER, HOST_BROKER, EXCHANGE_NAME
from consumers import control_consumer

redisClient = redis.Redis(host=HOST_CACHE_MASTER)
mongoClient = MongoClient(HOST_CONTROL_DB)


def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=HOST_BROKER))
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name)

    print('CONTROL WORKER: waiting for requests. To exit press CTRL+C')

    channel.basic_consume(queue=queue_name, on_message_callback=control_consumer, auto_ack=True)

    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
