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
import aiohttp

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
import redis

from .jwt_auth import oauth2_scheme, get_username_from_token

SERVER_URL = os.getenv("SERVER_URL", "websocket_server_1:80")

# Kafka configuration
TOPIC = "messages"
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka-1:9092")
PRODUCER_CONFIG = {
    "bootstrap.servers": KAFKA_BROKER,
    "client.id": "websocket-message-producer",
}
producer = Producer(PRODUCER_CONFIG)

# Redis configuration
redis_instance = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

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

class ChannelRequest(BaseModel):
    """
    This class defines a channel request.
    It is used to handle channel-related operations like joining, creating, or getting channels information.
    """
    operation: int  # 0 = join, 1 = create, 2 = get_user_channels, 3 = get_by_name
    channel_id: int = None
    channel_name: str = None
    description: str = None

class Request(BaseModel):
    """
    This class defines the request sent by the client.
    The client can request send a message or a channel request.
    """
    type: int # 0 = message, 1 = channel
    data: str


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
        """
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, username: str, websocket: WebSocket):

        active_connection = redis_instance.hget("active_connections", username)

        if active_connection:
            await websocket.accept()

            await websocket.send_text(json.dumps({
                "status": "error",
                "reason": "Already connected",
                "message": f"User {username} already has an active connection"
            }))

            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User already has an active connection")
            return False

        await websocket.accept()
        self.active_connections[username] = websocket
        redis_instance.hset("active_connections", username, SERVER_URL)

        return True

    def disconnect(self, username):
        if username in self.active_connections:
            del self.active_connections[username]
            redis_instance.hdel("active_connections", username)


manager = ConnectionManager()


async def send_message_to_server(message_str: str, websocket: WebSocket):
    try:
        # Parse the data
        data = json.loads(message_str)
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
        await websocket.send_text(json.dumps({"error": "Invalid JSON format for message request"}))

    except ValueError as e:
        await websocket.send_text(
            json.dumps({"error": f"Invalid message format: {str(e)}"})
        )

    except Exception as e:
        await websocket.send_text(
            json.dumps({"error": f"Failed to process message, error: {str(e)}"})
        )

# todo: separate this function in small functions or reuse code. Also might be good if this is in a separate file
async def send_channel_request(request_str: str, username: str, websocket: WebSocket):
    channel_server_url = "http://channel_manager:80/channels/"

    try:
        data = json.loads(request_str)
        channel_request = ChannelRequest(**data)

        async with aiohttp.ClientSession() as session:
            if channel_request.operation == 0:
                # Join channel
                join_url = channel_server_url + "join"
                data = {
                    "channel_id": channel_request.channel_id,
                    "username": username
                }
                try:
                    async with session.post(join_url, json=data, headers={"Content-Type": "application/json"}) as response:
                        response.raise_for_status()
                        result = await response.json()
                        await websocket.send_text(json.dumps(result))
                except aiohttp.ClientError as e:
                    await websocket.send_text(json.dumps({
                        "error": f"Failed to join channel: {str(e)}"
                    }))

            elif channel_request.operation == 1:
                # Create channel
                data = {
                    "channel_name": channel_request.channel_name,
                    "channel_description": channel_request.description if channel_request.description else ""
                }
                try:
                    async with session.post(channel_server_url, json=data, headers={"Content-Type": "application/json"}) as response:
                        response.raise_for_status()
                        result = await response.json()
                        await websocket.send_text(json.dumps(result))
                except aiohttp.ClientError as e:
                    await websocket.send_text(json.dumps({
                        "error": f"Failed to create channel: {str(e)}"
                    }))

            elif channel_request.operation == 2:
                # Get user channels
                get_user_channels_url = channel_server_url + "me/" + username
                try:
                    async with session.get(get_user_channels_url) as response:
                        response.raise_for_status()
                        result = await response.json()
                        await websocket.send_text(json.dumps(result))
                except aiohttp.ClientError as e:
                    await websocket.send_text(json.dumps({
                        "error": f"Channel request failed: {str(e)}"
                    }))

            elif channel_request.operation == 3:
                # Get channel by name
                get_by_name_url = channel_server_url + channel_request.channel_name
                try:
                    async with session.get(get_by_name_url) as response:
                        response.raise_for_status()
                        result = await response.json()
                        await websocket.send_text(json.dumps(result))
                except aiohttp.ClientError as e:
                    await websocket.send_text(json.dumps({
                        "error": f"Failed to get channel by name: {str(e)}"
                    }))
            else:
                await websocket.send_text(json.dumps({"error": f"Unknown operation: {channel_request.operation}"}))

    except json.JSONDecodeError as e:
        await websocket.send_text(json.dumps({"error": "Invalid JSON format for channel request. " + str(e)}))
    except Exception as e:
        await websocket.send_text(json.dumps({"error": f"Channel request processing failed: {str(e)}"}))

@app.get("/")
async def root():
    return {"hello_world": "Hello World!",
            "websocket_url": SERVER_URL
            }


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
    connected = await manager.connect(username, websocket)

    if not connected:
        return

    try:
        while True:
            data_str = await websocket.receive_text()

            try:
                data = json.loads(data_str)
                request = Request(**data)

                if request.type == 0:
                    await send_message_to_server(request.data, websocket)

                elif request.type == 1:
                    await send_channel_request(request.data, username, websocket)


            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON format"}))


    except WebSocketDisconnect:
        manager.disconnect(username)
    except Exception:
        manager.disconnect(username)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)


@app.post("/message")
async def send_message_to_client(message_request: MessageRequest):
    """
    This endpoint is used internally, the message server sends the message to this endpoint
    Then the message is sent to the client via websocket.
    """
    message = message_request.message
    username = message_request.username
    print(f"Sending message to {username}, message: {message.message}")

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

@app.get("/active-connections")
async def get_active_connections():
    return {"active_connections": list(manager.active_connections.keys())}