import redis
import pika
import sys
import os
import json
import time

from pymongo import MongoClient
from config import HOST_CONTROL_DB, HOST_CACHE_MASTER, HOST_BROKER, EXCHANGE_NAME

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

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    channel.start_consuming()


def callback(ch, method, properties, body):
    request = json.loads(body)
    proxy_db = mongoClient.proxy_db
    access_list = proxy_db.access_list

    doc = access_list.find_one({"type": "counter", "ip": request["ip"], "path": request["path"]})
    timestamp = int(time.time())
    if doc is None:
        access_list.insert_one(
            {"type": "counter", "ip": request["ip"], "path": request["path"], "count": 1, "first": timestamp,
             "last": timestamp})
    else:
        access_list.update_one({"_id": doc.get('_id')}, {'$inc': {'count': 1}, '$set': {'last': timestamp}})


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
