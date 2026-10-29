from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from backend.app.db import get_db
from backend.app.main import app
from backend.app.models import PasswordReset
from backend.app.routers import auth


def _register(client, email="a@test.com", password="secret123"):
    assert client.post("/auth/register", json={"email": email, "password": password}).status_code == 201


def _request_link(client, monkeypatch, email="a@test.com"):
    """Ask for a reset and capture the emailed link instead of sending it."""
    sent = []
    monkeypatch.setattr(auth, "send_reset_email", lambda to, link: sent.append((to, link)))
    r = client.post("/auth/forgot-password", json={"email": email})
    assert r.status_code == 200
    return sent


def test_reset_flow_changes_the_password(monkeypatch):
    client = TestClient(app)
    _register(client)
    sent = _request_link(client, monkeypatch)
    assert len(sent) == 1 and sent[0][0] == "a@test.com"
    token = sent[0][1].split("token=")[1]

    r = client.post("/auth/reset-password", json={"token": token, "password": "newsecret99"})
    assert r.status_code == 200
    assert client.post("/auth/login", data={"username": "a@test.com", "password": "secret123"}).status_code == 401
    assert client.post("/auth/login", data={"username": "a@test.com", "password": "newsecret99"}).status_code == 200


def test_unknown_email_gets_the_same_answer_and_no_email(monkeypatch):
    client = TestClient(app)
    known = _request_link(client, monkeypatch, "nobody@test.com")
    assert known == []
    r = client.post("/auth/forgot-password", json={"email": "nobody@test.com"})
    assert r.status_code == 200
    assert "reset link has been sent" in r.json()["message"]


def test_a_reset_link_works_only_once(monkeypatch):
    client = TestClient(app)
    _register(client)
    token = _request_link(client, monkeypatch)[0][1].split("token=")[1]
    assert client.post("/auth/reset-password", json={"token": token, "password": "newsecret99"}).status_code == 200
    assert client.post("/auth/reset-password", json={"token": token, "password": "another1234"}).status_code == 400


def test_expired_link_is_rejected(monkeypatch):
    client = TestClient(app)
    _register(client)
    token = _request_link(client, monkeypatch)[0][1].split("token=")[1]
    db = next(app.dependency_overrides[get_db]())
    row = db.query(PasswordReset).one()
    row.expires_at = datetime.utcnow() - timedelta(minutes=1)
    db.commit()
    r = client.post("/auth/reset-password", json={"token": token, "password": "newsecret99"})
    assert r.status_code == 400


def test_bad_token_and_short_password_are_rejected(monkeypatch):
    client = TestClient(app)
    _register(client)
    token = _request_link(client, monkeypatch)[0][1].split("token=")[1]
    assert client.post("/auth/reset-password", json={"token": "junk", "password": "newsecret99"}).status_code == 400
    assert client.post("/auth/reset-password", json={"token": token, "password": "short"}).status_code == 422