from confluent_kafka import Producer
import json
import uuid
from time import sleep
from datetime import datetime
from random import choice


TOPIC = "kafka-quickstart"
PRODUCER_CONFIG = {
    "bootstrap.servers": "localhost:19092,localhost:29092,localhost:39092",
    "client.id": f"kafka-quickstart-producer-{uuid.uuid4()}",
}

RANDOM_KEYS = [str(uuid.uuid4()) for _ in range(5)]

producer = Producer(PRODUCER_CONFIG)
while True:
    sleep(1)
    key = choice(RANDOM_KEYS)
    value = {"time": str(datetime.now()), "source": "kafka-quickstart-producer"}
    print(f"Producing {key} -> {value}\n\n")
    producer.produce(TOPIC, key=key, value=json.dumps(value))
