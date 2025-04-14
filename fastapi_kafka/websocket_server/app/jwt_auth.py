import os
import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError


# Configuration and constants
PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH")
ALGORITHM = os.getenv("ALGORITHM", "RS256")

# Load keys
PUBLIC_KEY = None

if PUBLIC_KEY_PATH and os.path.exists(PUBLIC_KEY_PATH):
    with open(PUBLIC_KEY_PATH, "rb") as key_file:
        PUBLIC_KEY = key_file.read()

# OAuth2 scheme for the JWT token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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