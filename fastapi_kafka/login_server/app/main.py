import os
from contextlib import asynccontextmanager
from typing import Annotated
from sqlmodel import Field, Session, SQLModel, create_engine, select

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel

from .jwt_auth import ACCESS_TOKEN_EXPIRATION, oauth2_scheme, create_access_token, get_username_from_token
from .database import SessionDep, create_db_and_tables, engine
from .models import User


class Token(BaseModel):
    access_token: str
    token_type: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    #create_db_and_tables()
    yield
    # shutdown

app = FastAPI(lifespan=lifespan)

@app.get("/db-check")
def check_db():
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names(schema="public")
    return {"tables": tables}



def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)


def get_user(session: Session, username: str) -> User | None:
    user = session.get(User, username)
    return user


def authenticate_user(session: Session, username: str, password: str):
    user = get_user(session, username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user



async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = get_username_from_token(token)

    user = get_user(session, username=username)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep) -> Token:
    user = authenticate_user(session, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=ACCESS_TOKEN_EXPIRATION
    )

    return Token(access_token=access_token, token_type="bearer")

@app.post("/users/", response_model=User)
def create_user(username: str, first_name: str, last_name: str,
                email: str, password: str, session: SessionDep):
    db_user = get_user(session, username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(password)
    db_user = User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=hashed_password
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/users/me")
async def read_user_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@app.get("/items/")
async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}


