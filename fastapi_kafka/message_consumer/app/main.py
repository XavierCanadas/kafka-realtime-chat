#
#  main.py
#  fastapi_kafka
#
#  Created by Xavier Cañadas on 15/4/2025
#  Copyright (c) 2025. All rights reserved.
from pydantic import BaseModel
from confluent_kafka import Consumer, KafkaException
from sqlmodel import Field, Session, SQLModel, create_engine, select

import logging
import json
import os
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Consumer configuration
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "kafka-1:9092")

MESSAGE_CONSUMER_CONFIG = {
    "bootstrap.servers": KAFKA_BROKER,
    "group.id": "websocket-message-producer",
    "auto.offset.reset": "latest", # during restarts, only read messages that haven't been processed.
}

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://root:password@relational_database:5433/chatdb"
)

engine = create_engine(DATABASE_URL, echo=True)

class MessageRequest(BaseModel):
    """
    This class defines the message sent by the client.
    """
    message_id: str
    channel_id: str
    timestamp: str
    username: str
    message: str

    def to_json_str(self):
        return json.dumps(self.model_dump())

message_consumer = Consumer(MESSAGE_CONSUMER_CONFIG)

running = True


def shutdown():
    global running
    running = False

def get_channel_users(channel_id: str) -> list[str]:
    """
    This function gets the usernames of all users in the channel.
    Makes the request to the relational database.
    todo: in the future might be changed to optimize the process, caching the info or something.
    """



def process_message(message: MessageRequest):
    """
    This function is called when a message is received from the Kafka broker.
    Steps:
        1. The consumer needs to get users that are in the channel.
        2. Then, get the active users and in witch websocket server are connected.
        3. Next, will send the message to all websocket servers.
        4. Finally, will store the message in the NoSQL database.
    """




def message_consumer_loop():
    """
    This function will contain the main logic of the message consumer.
    The consumer will read every message of its assigned partitions and then will process them.
    For each message, calls process_message function.
    """
    try:
        message_consumer.subscribe(["messages"])
        logger.info("Message consumer started")

        while running:
            new_message = message_consumer.poll(timeout=1.0)

            if new_message is None:
                continue

            if new_message.error():
                raise KafkaException(new_message.error())
            else:
                try:
                    message_info = json.loads(new_message.value())
                    process_message(MessageRequest(**message_info))

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON format: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")



    except KafkaException as e:
        logger.error(f"Error processing message: {e}")
    finally:
        message_consumer.close()
        logger.info("Message consumer closed")