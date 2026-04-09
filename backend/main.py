import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

import database
from ai import chat as ai_chat

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
USERNAME = "user"
PASSWORD = "password"


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


# --- helpers ---

def _require_auth(request: Request) -> str:
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# --- auth ---

class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
def login(body: LoginRequest, request: Request):
    if body.username == USERNAME and body.password == PASSWORD:
        request.session["user"] = body.username
        return {"ok": True}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/api/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@app.get("/api/auth/me")
def me(request: Request):
    user = _require_auth(request)
    return {"username": user}


# --- health ---

@app.get("/api/health")
def health():
    return {"status": "ok"}


# --- board ---

@app.get("/api/board")
def get_board(request: Request):
    user = _require_auth(request)
    return database.get_board(user)


@app.put("/api/board")
async def put_board(request: Request):
    user = _require_auth(request)
    data = await request.json()
    database.save_board(user, data)
    return {"ok": True}


# --- ai ---

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@app.post("/api/ai/test")
def ai_test():
    response = ai_chat("What is 2+2?", [], {})
    return {"response": response.message}


@app.post("/api/ai/chat")
async def ai_chat_route(body: ChatRequest, request: Request):
    user = _require_auth(request)
    board = database.get_board(user)
    response = ai_chat(body.message, body.history, board)
    if response.board_update is not None:
        database.save_board(user, response.board_update)
    return {"message": response.message, "board_updated": response.board_update is not None}


# --- static files ---

@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    candidate = os.path.join(STATIC_DIR, full_path)
    if os.path.isfile(candidate):
        return FileResponse(candidate)
    index = os.path.join(STATIC_DIR, full_path, "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
