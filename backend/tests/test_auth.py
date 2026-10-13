from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db import Base, get_db
from backend.app.main import app


def make_client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    return TestClient(app)


def test_register_login_me_flow():
    client = make_client()
    r = client.post("/auth/register", json={"email": "A@Test.com", "password": "secret123"})
    assert r.status_code == 201
    assert r.json()["email"] == "a@test.com"

    # duplicate email is rejected
    r = client.post("/auth/register", json={"email": "a@test.com", "password": "secret123"})
    assert r.status_code == 409

    # wrong password is rejected
    r = client.post("/auth/login", data={"username": "a@test.com", "password": "wrongpass1"})
    assert r.status_code == 401

    # correct login gives a token, and the token identifies the user
    r = client.post("/auth/login", data={"username": "a@test.com", "password": "secret123"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "a@test.com"

    # no token / bad token is rejected
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer junk"}).status_code == 401

    app.dependency_overrides.clear()