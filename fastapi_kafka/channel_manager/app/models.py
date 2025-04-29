#
#  models.py
#  fastapi_kafka
#
#  Created by Xavier Cañadas on 24/4/2025
#  Copyright (c) 2025. All rights reserved.
import os
from sqlmodel import Field, SQLModel
from datetime import datetime
from pydantic import BaseModel, BeforeValidator, ConfigDict
from typing import Optional, Annotated, List

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]

class Message(BaseModel):
    """
    This class defines the message sent by the client.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    message_id: Optional[str] = None  # created by the client. todo: is a good practice keeping both?
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

class MessageCollection(BaseModel):
    """
    This class defines the container holding a list of Message instances.
    """
    messages: List[Message] = Field(...)

class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    username: str = Field(primary_key=True)
    first_name: str
    last_name: str
    email: str = Field(unique=True)
    password_hash: str
    disabled: bool = Field(default=False)

class Channel(SQLModel, table=True):
    __tablename__ = "channels"
    __table_args__ = {"schema": "public"}

    id: int | None = Field(default=None, primary_key=True) # default is none so the database sets the id
    channel_name: str
    description: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class UserChannels(SQLModel, table=True):
    __tablename__ = "user_channels"
    __table_args__ = {"schema": "public"}

    username: str = Field(primary_key=True, foreign_key='public.users.username')
    channel_id: int = Field(primary_key=True, foreign_key='public.channels.id')


class CreateChannelRequest(BaseModel):
    channel_name: str
    channel_description: str

class JoinChannelRequest(BaseModel):
    channel_id: int
    username: str

