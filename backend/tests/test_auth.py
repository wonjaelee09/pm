import os
import tempfile

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
    return TestClient(app, raise_server_exceptions=True)


def test_me_unauthenticated(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_login_invalid_credentials(client):
    res = client.post("/api/auth/login", json={"username": "user", "password": "wrong"})
    assert res.status_code == 401


def test_login_success(client):
    res = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert res.status_code == 200
    assert res.json() == {"ok": True}


def test_me_after_login(client):
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    res = client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json() == {"username": "user"}


def test_logout(client):
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    res = client.post("/api/auth/logout")
    assert res.status_code == 200
    res = client.get("/api/auth/me")
    assert res.status_code == 401
