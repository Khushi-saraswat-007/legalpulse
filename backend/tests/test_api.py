import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from fastapi.testclient import TestClient
from backend.app.main import app


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_mock_report():
    r = TestClient(app).get("/contracts/c001/report")
    assert r.status_code == 200 and "risks" in r.json()
