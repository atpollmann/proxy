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
    request = json.loads(body)

    if request["allow"]:
        process_request(body)


def process_request(body):
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
            # If is a rule, insert counter and return
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
            return
        else:
            # It's a counter, increment it
            access_list.update_one(
                {"_id": docs[0]["_id"]},
                {'$inc': {'count': 1}, '$set': {'last': timestamp}}
            )
    else:
        # We have a rule AND a counter that must be processed
        rule = list(filter((lambda item: item["type"] == "rule"), docs))[0]
        counter = list(filter((lambda item: item["type"] == "counter"), docs))[0]

        if can_continue(rule, counter):
            access_list.update_one(
                {"_id": counter["_id"]},
                {'$inc': {'count': 1}, '$set': {'last': timestamp}}
            )
        else:
            # Client exceeded rate. Deny access
            key = f"{rule['ip']}{rule['path']}"
            redisClient.set(key, "deny")
            redisClient.expire(key, 1 if rule["unit"] == "s" else 60)
            # And delete counter
            access_list.delete_one({"_id": counter["_id"]})


def can_continue(rule, counter):
    """
    This is the core of the proxy.
    It analyzes if the request can pass or must be
    throttled.

    If the request cannot pass because of a rule, we
    send a key in the cache master server pointing
    that this connection is forbidden.
    The cache master will propagate the key to
    all the replica nodes.

    A very primitive algorithm is proposed here.
    There's a lot of room to improve.

    :param rule: has a rate (int) and a unit of time that can be "s"
     for seconds and "m" for minutes
    :param counter: a counter has a count (int), a first (double)
     that represents the first connection time and a last (double)
     that represents the last connection time
    :return: boolean
    """

    time_window_seconds = counter["last"] - counter["first"]
    connections = counter["count"]
    # The first log into access list has the same "first" and "last"
    client_rate = 0 if time_window_seconds == 0 else connections / time_window_seconds
    rule_rate_seconds = rule["rate"] if rule["unit"] == "s" else rule["rate"] / 60

    access_list.insert_one({
        "type": "debug",
        "last": counter["last"],
        "first": counter["first"],
        "unit": rule["unit"],
        "time_window_seconds": time_window_seconds,
        "connections": connections,
        "client_rate": client_rate,
        "rule_rate_seconds": rule_rate_seconds
    })

    return client_rate < rule_rate_seconds


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
