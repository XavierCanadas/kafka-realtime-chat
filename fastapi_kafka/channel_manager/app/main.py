#
#  main.py
#  fastapi_kafka
#
#  Created by Xavier Cañadas on 21/4/2025
#  Copyright (c) 2025. All rights reserved.
from fastapi import FastAPI, Query, status, HTTPException
from contextlib import asynccontextmanager
from sqlmodel import inspect, select

from .database import SessionDep, engine, get_channels_from_user, get_channels_by_name, create_channel, join_channel
from .models import Channel, UserChannels, CreateChannelRequest, JoinChannelRequest

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
@app.get("/channels/me/{username}")
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
@app.post("/channels")
def create_channel_endpoint(new_channel: CreateChannelRequest, session: SessionDep):
    """
    This endpoint creates a channel with the given channel_name and description.
    params:
        channel_name str: the channel_name given by the user
        description str: the description given by the user
    """
    try:
        channel = create_channel(new_channel.channel_name, new_channel.channel_description, session)
        return channel
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error))

# join a channel
@app.post("/channels/join")
def join_channel_endpoint(join_channel_req: JoinChannelRequest, session: SessionDep):
    """
    This endpoint joins a channel with the given channel_id and the username.
    params:
        channel_id int: the channel_id given by the user
    """
    try:
        user_channel = join_channel(join_channel_req.channel_id, join_channel_req.username, session)
        return {"status": "success", "channel_id": user_channel}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error))



