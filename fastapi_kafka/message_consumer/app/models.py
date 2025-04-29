#
#  models.py
#  fastapi_kafka
#
#  Created by Xavier Cañadas on 28/4/2025
#  Copyright (c) 2025. All rights reserved.
from typing import Optional, Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict
from sqlmodel import Field, SQLModel

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]

class UserChannels(SQLModel, table=True):
    __tablename__ = "user_channels"
    __table_args__ = {"schema": "public"}

    username: str = Field(primary_key=True, foreign_key='users.username')
    channel_id: int = Field(primary_key=True, foreign_key='channels.channel_id')


class Message(BaseModel):
    """
    This class defines the message sent by the client.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    message_id: str = Field(...) # created by the client. todo: is a good practice keeping both?
    channel_id: int = Field(...)
    timestamp: str = Field(...)
    username: str = Field(...)
    message: str = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "message_id": "...",
                "channel_id": 1,
                "timestamp": "2025-04-28T14:30:00Z",
                "username": "user123",
                "message": "Hello, world!"
            }
        },
    )


class MessageRequest(BaseModel):
    """
    This class defines a message request.
    This allows putting more info in the post if it's necessary in the future.
    """
    message: Message
    username: str | None