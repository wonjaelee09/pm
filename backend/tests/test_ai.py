"""
Tests for AI module. Live API calls are skipped when OPENROUTER_API_KEY is absent.
"""
import json
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import database
from ai import AIResponse, chat


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    database.DB_PATH = str(tmp_path / "test.db")
    database.init_db()
    yield
    database.DB_PATH = "kanban.db"


@pytest.fixture
def auth_client():
    from main import app
    client = TestClient(app)
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    return client


def _make_mock_completion(content: str):
    choice = MagicMock()
    choice.message.content = content
    completion = MagicMock()
    completion.choices = [choice]
    return completion


def test_chat_no_board_update():
    payload = json.dumps({"message": "Hello!", "board_update": None})
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _make_mock_completion(payload)

    with patch("ai.OpenAI", return_value=mock_client):
        result = chat("Hello!", [], {})

    assert result.message == "Hello!"
    assert result.board_update is None


def test_chat_with_board_update():
    board = {"columns": [], "cards": {}}
    payload = json.dumps({"message": "Done!", "board_update": board})
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _make_mock_completion(payload)

    with patch("ai.OpenAI", return_value=mock_client):
        result = chat("Move card", [], {})

    assert result.message == "Done!"
    assert result.board_update == board


def test_chat_malformed_json_falls_back():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _make_mock_completion("not json")

    with patch("ai.OpenAI", return_value=mock_client):
        result = chat("Hello", [], {})

    assert result.message == "not json"
    assert result.board_update is None


def test_api_chat_unauthenticated():
    from main import app
    client = TestClient(app)
    res = client.post("/api/ai/chat", json={"message": "hi", "history": []})
    assert res.status_code == 401


def test_api_chat_updates_board(auth_client):
    initial_board = auth_client.get("/api/board").json()
    updated_board = {**initial_board, "columns": [{**initial_board["columns"][0], "title": "AI Changed"}] + initial_board["columns"][1:]}
    payload = json.dumps({"message": "Done!", "board_update": updated_board})

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _make_mock_completion(payload)

    with patch("ai.OpenAI", return_value=mock_client):
        res = auth_client.post("/api/ai/chat", json={"message": "change title", "history": []})

    assert res.status_code == 200
    body = res.json()
    assert body["board_updated"] is True
    assert body["message"] == "Done!"

    board = auth_client.get("/api/board").json()
    assert board["columns"][0]["title"] == "AI Changed"


@pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="No API key")
def test_live_ai_call():
    result = chat("What is 2+2? Respond only with the number.", [], {})
    assert "4" in result.message
