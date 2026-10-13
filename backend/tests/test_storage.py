from fastapi.testclient import TestClient
from backend.app.main import app

OLD = b"""AGREEMENT

1. Payment. Buyer shall pay each invoice within 30 days of the invoice date.

2. Late Payment. If Buyer fails to pay under Section 1, interest of 2% per month applies.

3. Termination. Either party may terminate this agreement on 30 days notice. Section 2 survives termination.

4. Governing Law. This agreement is governed by the laws of India and the parties submit to its courts.
"""
NEW = OLD.replace(b"within 30 days", b"within 60 days")


def _upload(c, headers, key="k1"):
    return c.post("/contracts/analyze", data={"contract_key": key}, headers=headers,
                  files={"old_file": ("old.txt", OLD, "text/plain"), "new_file": ("new.txt", NEW, "text/plain")})


def test_analysis_is_saved_and_listed(auth_headers):
    c = TestClient(app)
    assert c.get("/contracts", headers=auth_headers).json() == []
    r = _upload(c, auth_headers)
    assert r.status_code == 200 and r.json()["analysis_id"] == 1
    _upload(c, auth_headers, "k2")
    rows = c.get("/contracts", headers=auth_headers).json()
    assert [x["contract_key"] for x in rows] == ["k2", "k1"]        # newest first
    assert rows[0]["n_changes"] == 1 and rows[0]["old_filename"] == "old.txt"


def test_get_saved_report_and_404(auth_headers):
    c = TestClient(app)
    _upload(c, auth_headers)
    full = c.get("/contracts/1", headers=auth_headers).json()
    assert full["analysis_id"] == 1 and full["risks"][0]["rank"] == 1
    assert c.get("/contracts/999", headers=auth_headers).status_code == 404


def test_login_required():
    c = TestClient(app)
    assert c.get("/contracts").status_code == 401
    assert c.get("/contracts/1").status_code == 401
    r = c.post("/contracts/analyze",
               files={"old_file": ("old.txt", OLD), "new_file": ("new.txt", NEW)})
    assert r.status_code == 401


def test_users_only_see_their_own(auth_headers, other_headers):
    c = TestClient(app)
    _upload(c, auth_headers)
    assert len(c.get("/contracts", headers=auth_headers).json()) == 1
    assert c.get("/contracts", headers=other_headers).json() == []
    assert c.get("/contracts/1", headers=other_headers).status_code == 404
    assert c.get("/contracts/1", headers=auth_headers).status_code == 200


def test_stats(auth_headers, other_headers):
    c = TestClient(app)
    assert c.get("/contracts/stats", headers=auth_headers).json()["contracts"] == 0
    _upload(c, auth_headers)
    s = c.get("/contracts/stats", headers=auth_headers).json()
    assert s["contracts"] == 1 and s["changes"] == 1
    assert c.get("/contracts/stats", headers=other_headers).json()["contracts"] == 0
    assert c.get("/contracts/stats").status_code == 401