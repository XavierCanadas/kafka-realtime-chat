#
#  database.py
#  fastapi_kafka
#
#  Created by Xavier Cañadas on 24/4/2025
#  Copyright (c) 2025. All rights reserved.
import os
from typing import Annotated, Sequence
import json
from bson import ObjectId, json_util
from pydantic import BeforeValidator

from sqlmodel import create_engine, Session, select
from sqlmodel.sql._expression_select_cls import _T
from sqlalchemy import Select
from fastapi import Depends, HTTPException
from pymongo import MongoClient, DESCENDING

from .models import Channel, UserChannels, Message, PyObjectId, MessageCollection

# Init postgres database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://root:password@relational_database:5432/chatdb"
)
engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

# Init mongodb
MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://root:password@mongodb:27017/")
client = MongoClient(MONGODB_URL)
db = client.chatdb
messages_collection = db.messages



"""
SELECT c.*
FROM channels c
JOIN user_channels uc ON uc.channel_id = c.id
WHERE uc.username = 'username';
"""


def get_channels_from_user(username: str, session: SessionDep) -> Sequence[_T] | list[Channel]:
    """
    This function returns a list of channels whose username matches the given username.
    params:
        username (str): The username to search for
    returns:
        list[Channel]: The channels whose username matches the given username
    """
    try:
        statement: Select = select(Channel).join(UserChannels).where(UserChannels.username == username)
        channels = session.exec(statement).all()
        print(channels)
        return channels

    except Exception as e:
        raise e


def get_channels_by_name(channel_name: str, session: SessionDep) -> Sequence[_T] | list[Channel]:
    """
    This function returns a list of channels whose chanel_name matches the given channel_name.
    params:
        channel_name (str): The channel name to search for
    returns:
        list[Channel]: The channels whose chanel_name matches the given channel_name
    """
    try:
        statement: Select = select(Channel).where(Channel.channel_name == channel_name)
        channels = session.exec(statement).all()
        print(channels)
        return channels
    except Exception as e:
        raise e


def create_channel(channel_name: str, description: str, session: SessionDep) -> Channel:
    if not channel_name or not description:
        raise Exception("channel_name and description are required")

    try:
        channel = Channel(channel_name=channel_name, description=description)
        session.add(channel)
        session.commit()
        session.refresh(channel)
        return channel
    except Exception as e:
        raise Exception(e)


def join_channel(channel_id: int, username: str, session: Session) -> UserChannels:
    if not channel_id or not username:
        raise Exception("channel_id and username are required")

    # check if the user is already in the channel
    try:
        statement: Select = select(UserChannels).where(
            (UserChannels.channel_id == channel_id) & (UserChannels.username == username))
        result = session.exec(statement).all()
        if result:
            raise Exception("username already is in the channel")

    except Exception as e:
        raise Exception(e)

    try:
        user_channel = UserChannels(username=username, channel_id=channel_id)
        session.add(user_channel)
        session.commit()
        session.refresh(user_channel)
        return user_channel
    except Exception as e:
        raise Exception(e)


# todo: implement pagination within a datetime.
def get_channel_messages_history(channel_id: int, limit: int = 50) -> MessageCollection:
    try:
        channel_messages = (messages_collection.find({"channel_id": channel_id})
                    .sort("timestamp", DESCENDING)).to_list(limit)
        return MessageCollection(messages=channel_messages)

    except Exception as e:
        raise e
