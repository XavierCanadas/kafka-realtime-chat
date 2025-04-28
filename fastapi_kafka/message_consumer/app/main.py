#
#  main.py
#  fastapi_kafka
#
#  Created by Xavier Cañadas on 15/4/2025
#  Copyright (c) 2025. All rights reserved.
from typing import Any, Sequence

from pydantic import BaseModel
from confluent_kafka import Consumer, KafkaException
from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlalchemy import Select

import logging
import json
import os
import requests
import aiohttp
from sqlmodel.sql._expression_select_cls import _T
import redis
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Consumer configuration
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "kafka-1:9092")

MESSAGE_CONSUMER_CONFIG = {
    "bootstrap.servers": KAFKA_BROKER,
    "group.id": "websocket-message-producer",
    "auto.offset.reset": "latest",  # during restarts, only read messages that haven't been processed.
}

# Redis configuration
redis_instance = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)


# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://root:password@relational_database:5432/chatdb"
)

engine = create_engine(DATABASE_URL, echo=True)

"""
CREATE TABLE IF NOT EXISTS user_channels
(
    username   VARCHAR(50) NOT NULL,
    channel_id INTEGER     NOT NULL,
    PRIMARY KEY (username, channel_id),
    FOREIGN KEY (username) REFERENCES users (username) ON DELETE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES channels (id) ON DELETE CASCADE
);
"""

class UserChannels(SQLModel, table=True):
    __tablename__ = "user_channels"
    __table_args__ = {"schema": "public"}

    username: str = Field(primary_key=True, foreign_key='users.username')
    channel_id: int = Field(primary_key=True, foreign_key='channels.channel_id')


class Message(BaseModel):
    """
    This class defines the message sent by the client.
    """
    message_id: str
    channel_id: int
    timestamp: str
    username: str
    message: str


class MessageRequest(BaseModel):
    """
    This class defines a message request.
    This allows putting more info in the post if it's necessary in the future.
    """
    message: Message
    username: str | None


message_consumer = Consumer(MESSAGE_CONSUMER_CONFIG)

running = True


def shutdown():
    global running
    running = False


def get_channel_users(channel_id: int) -> Sequence[_T] | list[Any]:
    """
    This function gets the usernames of all users in the channel.
    Makes the request to the relational database.
    params:
        channel_id (int): The channel id.
    returns:
        list[str]: a list of all usernames in the channel. The specification Sequence[_T] | list[Any] is to avoid warnings.

    todo: in the future might be changed to optimize the process, caching the info or something.

    The sql request is:
        SELECT uc.username
        FROM user_channels uc
        WHERE uc.channel_id = 1;
    """
    with Session(engine) as session:
        try:
            statement: Select = select(UserChannels.username).where(
                UserChannels.channel_id == channel_id
            )
            result = session.exec(statement).all()
            logger.info(f"usernames: {result}")
            return result
        except Exception as e:
            logger.error(e)
            return []


def get_user_websocket_server(username: str) -> str | None:
    """
    This function gets the websocket server for the given username.
    Makes the request to the Redis database.
    params:
        username (str): The username to get the websocket server for.
    returns:
        str: The websocket server url for the given username.

    todo: now will always return the same websocket server and without consulting Redis, in the future change it.
    """
    websocket_server_url = redis_instance.hget("active_connections", username)
    if websocket_server_url:
        return websocket_server_url

    return None

async def send_message(message: Message, username: str, websocket_server_url: str):
    """
    This function sends the given message to the websocket server with the given url.
    The message will be sent with a post, header = application/json.
    Now the function does not contemplate the return of the request.

    params:
        message (Message): The message to send.
        websocket_server_url (str): The url of the websocket server.
    """
    message_request = MessageRequest(message=message, username=username)

    header = {"Content-Type": "application/json"}
    data = message_request.model_dump()

    async with aiohttp.ClientSession() as session:
        try:
            url = f"http://{websocket_server_url}/message"
            async with session.post(url, json=data, headers=header) as response:
                response.raise_for_status()

                if response.status != 200:
                    logger.error(response.text)

        except Exception as e:
            logger.error(f"Failed to send message: {e}")


async def store_message(message: Message):
    """
    This function stores the given message in the non relational database.
    todo: now the function doesn't do anything, in the future make it functional.
    """
    logger.info(
        f"message stored in the database: {message.message_id}: {message.message}"
    )


async def process_message(message: Message):
    """
    This function is called when a message is received from the Kafka broker.
    Steps:
        1. The consumer needs to get users that are in the channel.
        2. Then, send the message to all users in the channel (not just the message sender).
        3. Finally, store the message in the NoSQL database.
    """
    # Get all users in the channel
    usernames = get_channel_users(message.channel_id)
    logger.info(
        f"Distributing message to all users in channel {message.channel_id}: {usernames}"
    )

    # Send message to ALL users in the channel, not just the sender
    for username in usernames:
        try:
            websocket_server = get_user_websocket_server(username)
            logger.info(f"Sending message to user: {username}")
            if websocket_server:
                await send_message(message, username, websocket_server)
        except Exception as e:
            logger.error(f"Failed to send message to {username}: {e}")

    # Store the message for history
    await store_message(message)


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
                    logger.info(f"Message info: {message_info}")
                    asyncio.run(process_message(Message(**message_info)))

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON format: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

    except KafkaException as e:
        logger.error(f"Error processing message: {e}")
    finally:
        message_consumer.close()
        logger.info("Message consumer closed")


if __name__ == "__main__":
    message_consumer_loop()
