#
#  main.py
#  fastapi_kafka
#
#  Created by Xavier Cañadas on 15/4/2025
#  Copyright (c) 2025. All rights reserved.

from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Annotated
import json
import os

from fastapi import (
    FastAPI,
    Query,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from confluent_kafka import Producer, Consumer, KafkaError

from .jwt_auth import oauth2_scheme, get_username_from_token

TOPIC = "messages"

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka-1:9092")

PRODUCER_CONFIG = {
    "bootstrap.servers": KAFKA_BROKER,
    "client.id": "websocket-message-producer",
}

producer = Producer(PRODUCER_CONFIG)

"""
Message sent by the client
{
    "message_id": str,
    "channel_id": str,
    "timestamp": str,
    "username": str,
    "message": str,
}
"""


# todo: in the future maybe would need to create a Request class, to allow different tipes of requests: message, history of a channel…
# for now, the only requests the client will send are messages.


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
    This allows putting more info in the post if it's necessary in the future, like replication or other websockets to send…
    """
    message: Message
    username: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup

    yield
    # shutdown
    producer.flush()  # before shutdown, the producer needs to send the pending messages


app = FastAPI()


class ConnectionManager:
    def __init__(self):
        """
        active_connections: dics of the websocket connections. The username is the key and the WebSocket the value.
        todo: in the future would change to use redis.
        """
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, username: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[username] = websocket

    def disconnect(self, username):
        del self.active_connections[username]


manager = ConnectionManager()


@app.get("/")
async def root():
    return {"hello_world": "Hello World!"}


@app.websocket("/ws")
async def websocket_endpoint(
    *,
    websocket: WebSocket,
    token: Annotated[str, Query()],
):
    # Check if the token is valid
    try:
        username = get_username_from_token(token)
    except Exception as error:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    # Store the connection in the manager
    await manager.connect(username, websocket)

    try:
        while True:
            data_str = await websocket.receive_text()

            try:
                # Parse the data
                data = json.loads(data_str)
                message = Message(**data)

                # todo: maybe send the MessageRequest in kafka instead of Message.
                # Send the message to Kafka
                producer.produce(
                    TOPIC, key=str(message.channel_id), value=message.model_dump_json()
                )
                producer.poll(1)

                # Send acknowledgment to the client
                await websocket.send_text(
                    json.dumps({"status": "sent", "message_id": message.message_id})
                )

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON format"}))
            except ValueError as e:
                await websocket.send_text(
                    json.dumps({"error": f"Invalid message format: {str(e)}"})
                )
            except Exception as e:
                await websocket.send_text(
                    json.dumps({"error": f"Failed to process message, error: {str(e)}"})
                )

    except WebSocketDisconnect:
        manager.disconnect(username)
    except Exception:
        manager.disconnect(username)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)


@app.post("/message/")
async def send_message_to_client(message_request: MessageRequest):
    """
    This endpoint is used internally, the message server sends the message to this endpoint
    Then the message is sent to the client via websocket.
    """
    message = message_request.message
    username = message_request.username
    print("AAA")
    # Check if the user is connected
    if username not in manager.active_connections:
        return {"error": "User not connected"}

    if username == message.username:
        return {"error": f"Invalid username, {username} is the sender"}

    try:
        # Send the message to the client
        websocket = manager.active_connections[username]
        await websocket.send_text(message.model_dump_json())

        return {"status": "sent", "message_id": message.message_id}
    except Exception as e:
        return {"status": "error", "reason": f"Unexpected error: {str(e)}"}

@app.get("/active-connections/")
async def get_active_connections():
    return {"active_connections": list(manager.active_connections.keys())}