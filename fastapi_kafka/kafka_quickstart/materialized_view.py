from confluent_kafka import Consumer, KafkaError
import json
import uuid
from time import sleep
from datetime import datetime


TOPIC = "kafka-quickstart"
CONSUMER_CONFIG = {
    "bootstrap.servers": "localhost:19092,localhost:29092,localhost:39092",
    "group.id": f"kafka-quickstart-consumer-{uuid.uuid4()}",
    "auto.offset.reset": "earliest",
}


consumer = Consumer(CONSUMER_CONFIG)
materialized_view = {}

try:
    consumer.subscribe([TOPIC])

    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue

        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                print("end of partition")
                continue
            elif msg.error():
                raise ValueError(msg.error())

        key = msg.key().decode()
        value = msg.value()

        if value is None:
            # delete
            if key in materialized_view:
                materialized_view.pop(key)
        else:
            # create
            value_dict = json.loads(value.decode())
            materialized_view[key] = value_dict

        print()
        print("--- Materialized view summary ---")
        for key, value in materialized_view.items():
            print(f"{key}: {value['time']}")
        print("---------------------------------")
        print()
finally:
    # Close down consumer to commit final offsets.
    consumer.close()
