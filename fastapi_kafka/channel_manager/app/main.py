#
#  main.py
#  fastapi_kafka
#
#  Created by Xavier Cañadas on 21/4/2025
#  Copyright (c) 2025. All rights reserved.
from fastapi.params import Depends
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Annotated
import json
import os

from fastapi import FastAPI, Query, status, HTTPException
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from sqlmodel import inspect, select

from .database import SessionDep, engine, get_channels_from_user, get_channels_by_name, create_channel, join_channel
from .models import Channel, UserChannels



@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown

app = FastAPI()

@app.get("/")
async def root():
    return {"hello_world": "Hello World!"}

@app.get("/db-check")
def check_db():
    inspector = inspect(engine)
    tables = inspector.get_table_names(schema="public")
    return {"tables": tables}

# given a user, return all the channels
@app.get("/channels/me")
def get_user_channels(username: str, session: SessionDep):
    """
    This endpoint returns all user's channels. When a user enters the app, calls this endpoint.
    params:
        username: The username of the user
    """

    try:
        channels = get_channels_from_user(username, session)
        return channels
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



# return channels given the name
@app.get("/channels/{channel_name}")
def get_channel(channel_name: str, session: SessionDep):
    """
    This endpoint returns all the channels with the given channel_name.
    params:
        channel_name str: the channel_name given by the user
        token Annotated[str, Depends(oauth2_scheme)]: the jwt token given by the user
    """
    try:
        channels = get_channels_by_name(channel_name, session)
        return channels
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# create a channel
@app.post("/channels", response_model=Channel)
def create_channel_endpoint(channel_name: str, description: str, session: SessionDep):
    """
    This endpoint creates a channel with the given channel_name and description.
    params:
        channel_name str: the channel_name given by the user
        description str: the description given by the user
    """
    try:
        channel = create_channel(channel_name, description, session)
        return channel
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error))

# join a channel
@app.post("/channels/join")
def join_channel_endpoint(channel_id: int, username: str, session: SessionDep):
    """
    This endpoint joins a channel with the given channel_id and the username.
    params:
        channel_id int: the channel_id given by the user
    """
    try:
        user_channel = join_channel(channel_id, username, session)
        return {"status": "success", "channel_id": user_channel}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error))



