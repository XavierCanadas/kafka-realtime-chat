#
#  models.py
#  fastapi_kafka
#
#  Created by Xavier Cañadas on 28/4/2025
#  Copyright (c) 2025. All rights reserved.

from pydantic import BaseModel

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
    operation: int  # 0 = join, 1 = create, 2 = get_user_channels, 3 = get_by_name, 4 = channel history
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