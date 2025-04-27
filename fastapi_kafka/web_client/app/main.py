#
#  main.py
#  fastapi_kafka
#
#  Created by GitHub Copilot on 16/4/2025
#  Copyright (c) 2025. All rights reserved.

import json
import uuid
from datetime import datetime
from typing import Annotated, Optional, Dict
import os

import requests
from fastapi import FastAPI, Request, Form, Cookie, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Configuration
LOGIN_SERVER_URL = os.getenv("LOGIN_SERVER_URL", "http://login_server")
WEBSOCKET_SERVER_URL = os.getenv("WEBSOCKET_SERVER_URL", "http://websocket_server_1")
WEBSOCKET_CLIENT_URL = os.getenv(
    "WEBSOCKET_CLIENT_URL", "ws://localhost:5001/ws"
)  # The URL clients use to connect

# Initialize FastAPI
app = FastAPI()

# Set up templates directory
templates = Jinja2Templates(directory="app/templates")

# Set up static files directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Session storage (in production this would be Redis or similar)
active_sessions: Dict[str, Dict] = {}


class LoginForm(BaseModel):
    username: str
    password: str


def get_current_user(session_id: Annotated[Optional[str], Cookie()] = None):
    """Dependency to check if user is logged in"""
    if not session_id or session_id not in active_sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return active_sessions[session_id]


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, session_id: Annotated[Optional[str], Cookie()] = None):
    """Render the login page or redirect to chat if already logged in"""
    if session_id and session_id in active_sessions:
        return RedirectResponse(url="/channels")

    return templates.TemplateResponse(
        "login.html", {"request": request, "error_message": ""}
    )


@app.post("/login")
async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    """Handle login form submission"""
    # Call login server to authenticate user
    try:
        response = requests.post(
            f"{LOGIN_SERVER_URL}/token",
            data={"username": username, "password": password},
        )

        if response.status_code != 200:
            # Return to login page with error
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": {"method": "POST"},
                    "error_message": "Invalid username or password",
                },
                status_code=401,
            )

        # Extract token from response
        token_data = response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": {"method": "POST"},
                    "error_message": "Authentication error",
                },
                status_code=401,
            )

        # Create session
        session_id = str(uuid.uuid4())
        active_sessions[session_id] = {
            "username": username,
            "token": access_token,
        }

        # Redirect to channels page with session cookie
        response = RedirectResponse(url="/channels", status_code=303)
        response.set_cookie(key="session_id", value=session_id)
        return response

    except Exception as e:
        return templates.TemplateResponse(
            "login.html",
            {"request": {"method": "POST"}, "error_message": f"Error: {str(e)}"},
            status_code=500,
        )


@app.get("/channels", response_class=HTMLResponse)
async def channels(request: Request, user_data: dict = Depends(get_current_user)):
    """Render the channels page"""
    return templates.TemplateResponse(
        "channels.html",
        {
            "request": request,
            "username": user_data["username"],
            "token": user_data["token"],
            "websocket_url": WEBSOCKET_CLIENT_URL,
        },
    )


@app.get("/chat/{channel_id}", response_class=HTMLResponse)
async def chat(
    request: Request, channel_id: int, user_data: dict = Depends(get_current_user)
):
    """Render the chat page for a specific channel"""
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "username": user_data["username"],
            "token": user_data["token"],
            "websocket_url": WEBSOCKET_CLIENT_URL,
            "channel_id": channel_id,
        },
    )


@app.get("/logout")
async def logout(session_id: Annotated[Optional[str], Cookie()] = None):
    """Handle user logout"""
    if session_id and session_id in active_sessions:
        del active_sessions[session_id]

    response = RedirectResponse(url="/")
    response.delete_cookie(key="session_id")
    return response
