#
#  channel_requests.py
#  fastapi_kafka
#
#  Created by Xavier Cañadas on 28/4/2025
#  Copyright (c) 2025. All rights reserved.
import json
import aiohttp
from fastapi import WebSocket

from .models import ChannelRequest


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