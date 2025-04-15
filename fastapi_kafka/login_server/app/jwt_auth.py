#
#  jwt_auth.py
#  fastapi_kafka
#
#  Created by Xavier Cañadas on 15/4/2025
#  Copyright (c) 2025. All rights reserved.

import os
from datetime import datetime, timedelta, timezone
from typing import Annotated
from sqlmodel import Field, SQLModel

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration and constants
PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH")
PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH")
ALGORITHM = os.getenv("ALGORITHM", "RS256")
ACCESS_TOKEN_EXPIRATION = timedelta(days=30)

# Load keys
PUBLIC_KEY = None
PRIVATE_KEY = None

if PUBLIC_KEY_PATH and os.path.exists(PUBLIC_KEY_PATH):
    with open(PUBLIC_KEY_PATH, "rb") as key_file:
        PUBLIC_KEY = key_file.read()

if PRIVATE_KEY_PATH and os.path.exists(PRIVATE_KEY_PATH):
    with open(PRIVATE_KEY_PATH, "rb") as key_file:
        PRIVATE_KEY = key_file.read()

# Models
class TokenData(BaseModel):
    username: str | None = None



# OAuth2 scheme for the JWT token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    if not PRIVATE_KEY:
        raise Exception("Private key not loaded.")

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def get_username_from_token(token: str):
    if not PUBLIC_KEY:
        raise Exception("Public key not loaded")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

        return username

    except InvalidTokenError:
        raise credentials_exception