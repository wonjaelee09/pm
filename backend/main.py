import os
import secrets
import sys
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

import database
from ai import chat as ai_chat

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
REAL_STATIC_DIR = os.path.realpath(STATIC_DIR)

# H2: warn and generate a random key rather than silently using a weak default
_env_key = os.getenv("SECRET_KEY")
if not _env_key:
    print(
        "WARNING: SECRET_KEY not set; using a random key. Sessions will not persist across restarts.",
        file=sys.stderr,
    )
    _env_key = secrets.token_hex(32)
SECRET_KEY = _env_key

# M6: allow https_only to be enabled via env var for HTTPS deployments
HTTPS_ONLY = os.getenv("HTTPS_ONLY", "false").lower() == "true"

USERNAME = "user"
PASSWORD = "password"


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, https_only=HTTPS_ONLY)


# --- helpers ---

def _require_auth(request: Request) -> str:
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# --- models ---

class LoginRequest(BaseModel):
    username: str
    password: str


class CardModel(BaseModel):
    id: str
    title: str
    details: str


class ColumnModel(BaseModel):
    id: str
    title: str
    cardIds: list[str]


# M2: typed board model so PUT /api/board validates structure before hitting the handler
class BoardDataModel(BaseModel):
    columns: list[ColumnModel]
    cards: dict[str, CardModel]


# M3: typed history so invalid role values are rejected with 422
class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[HistoryMessage] = []


# --- auth ---

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
def put_board(body: BoardDataModel, request: Request):
    user = _require_auth(request)
    database.save_board(user, body.model_dump())
    return {"ok": True}


# --- ai ---

# M1: /api/ai/test now requires auth to prevent unauthenticated API spend
@app.post("/api/ai/test")
def ai_test(request: Request):
    _require_auth(request)
    response = ai_chat("What is 2+2?", [], {})
    return {"response": response.message}


@app.post("/api/ai/chat")
def ai_chat_route(body: ChatRequest, request: Request):
    user = _require_auth(request)
    board = database.get_board(user)
    history = [{"role": m.role, "content": m.content} for m in body.history]
    response = ai_chat(body.message, history, board)
    if response.board_update is not None:
        database.save_board(user, response.board_update)
    return {"message": response.message, "board_updated": response.board_update is not None}


# --- static files ---

@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    # M5: guard against path traversal by verifying the resolved path stays within STATIC_DIR
    candidate = os.path.realpath(os.path.join(STATIC_DIR, full_path))
    if not (candidate == REAL_STATIC_DIR or candidate.startswith(REAL_STATIC_DIR + os.sep)):
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
    if os.path.isfile(candidate):
        return FileResponse(candidate)
    index = os.path.realpath(os.path.join(STATIC_DIR, full_path, "index.html"))
    if os.path.isfile(index) and index.startswith(REAL_STATIC_DIR):
        return FileResponse(index)
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
