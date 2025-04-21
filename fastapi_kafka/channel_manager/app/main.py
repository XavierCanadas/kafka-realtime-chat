#
#  main.py
#  fastapi_kafka
#
#  Created by Xavier Cañadas on 21/4/2025
#  Copyright (c) 2025. All rights reserved.
import datetime

from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Annotated
import json
import os

from fastapi import FastAPI, Query, status
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from .jwt_auth import oauth2_scheme, get_username_from_token


# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://root:password@relational_database:5432/chatdb"
)

engine = create_engine(DATABASE_URL, echo=True)
"""
CREATE TABLE IF NOT EXISTS channels
(
    id           SERIAL PRIMARY KEY,
    channel_name VARCHAR(50) UNIQUE NOT NULL,
    description  VARCHAR(255),
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
class Channel(SQLModel, table=True):
    __tablename__ = "channels"
    __table_args__ = {"schema": "chatdb"}

    id: int | None = Field(default=None, primary_key=True) # default is none so the database sets the id
    channel_name: str
    description: str
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown

app = FastAPI()

@app.get("/")
async def root():
    return {"hello_world": "Hello World!"}

