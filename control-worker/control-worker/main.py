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
proxy_db = mongoClient.proxy_db
access_list = proxy_db.access_list


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
    timestamp = time.time()
    request = json.loads(body)

    # Obtain all entry types only in one call: rules and counter
    docs = list(access_list.find({"ip": request["ip"], "path": request["path"]}))

    if len(docs) == 0:
        # We dont have any entry on the access list. Insert the first
        access_list.insert_one(
            {
                "type": "counter",
                "ip": request["ip"],
                "path": request["path"],
                "count": 1,
                "first": timestamp,
                "last": timestamp
            }
        )
    elif len(docs) == 1:
        if docs[0]["type"] == "rule":
            # If is a rule, continue
            return
        else:
            # It's a counter, increment it
            access_list.update_one(
                {"_id": docs[0]["_id"]},
                {'$inc': {'count': 1}, '$set': {'last': timestamp}}
            )
    else:
        # We have a rule AND a counter that must be processed
        process_request(docs)


def process_request(docs):
    access_list.insert_one(
        {
            "type": "log",
            "value": "got here"
        }
    )
    key = f"{docs[0]['ip']}{docs[0]['path']}"
    redisClient.set(key, "deny")
    redisClient.expire(key, 5)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
