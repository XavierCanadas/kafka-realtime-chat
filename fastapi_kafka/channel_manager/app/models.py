#
#  models.py
#  fastapi_kafka
#
#  Created by Xavier Cañadas on 24/4/2025
#  Copyright (c) 2025. All rights reserved.
import os
from sqlmodel import Field, SQLModel
from datetime import datetime
from pydantic import BaseModel



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

