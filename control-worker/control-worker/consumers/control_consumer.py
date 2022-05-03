def control_consumer(ch, method, properties, body):
    print("CONTROL CONSUMER: received %r" % body)
