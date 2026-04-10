import pytest
from fastapi.testclient import TestClient

import database


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    database.DB_PATH = str(tmp_path / "test.db")
    database.init_db()
    yield
    database.DB_PATH = "kanban.db"


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


@pytest.fixture
def auth_client(client):
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    return client


def test_get_board_unauthenticated(client):
    res = client.get("/api/board")
    assert res.status_code == 401


def test_get_board_returns_initial_data(auth_client):
    res = auth_client.get("/api/board")
    assert res.status_code == 200
    board = res.json()
    assert "columns" in board
    assert "cards" in board
    assert len(board["columns"]) == 5


def test_put_board_unauthenticated(client):
    res = client.put("/api/board", json={"columns": [], "cards": {}})
    assert res.status_code == 401


def test_put_board_persists(auth_client):
    board = auth_client.get("/api/board").json()
    board["columns"][0]["title"] = "Changed"
    res = auth_client.put("/api/board", json=board)
    assert res.status_code == 200

    updated = auth_client.get("/api/board").json()
    assert updated["columns"][0]["title"] == "Changed"
