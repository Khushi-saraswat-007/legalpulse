import os
import sys
import pathlib

os.environ["LEGALPULSE_EMBEDDER"] = "bow"          # fast, no model download in tests
os.environ["LEGALPULSE_NLI"] = "rule"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from fastapi.testclient import TestClient
from backend.app.main import app

OLD = b"""SUPPLY AGREEMENT

1. Payment. Buyer shall pay each invoice within 30 days of the invoice date.

2. Late Payment. If Buyer fails to pay under Section 1, interest of 2% per month applies.

3. Termination. Either party may terminate this agreement on 30 days notice. Section 2 survives termination.

4. Delivery. Supplier shall deliver the goods on or before the delivery date set in each order.

5. Governing Law. This agreement is governed by the laws of India and the parties submit to its courts.
"""
NEW = OLD.replace(b"within 30 days", b"within 60 days").replace(b"on 30 days notice", b"on 90 days notice")


def test_analyze_returns_ranked_risks(auth_headers):
    c = TestClient(app)
    r = c.post("/contracts/analyze", data={"contract_key": "t1"}, headers=auth_headers,
               files={"old_file": ("old.txt", OLD, "text/plain"), "new_file": ("new.txt", NEW, "text/plain")})
    assert r.status_code == 200, r.text
    rep = r.json()
    assert rep["meta"]["old_clauses"] == 5 and rep["risks"][0]["rank"] == 1
    kinds = [c["change_type"] for c in rep["changes"]]
    assert kinds.count("modified") == 2


def test_rejects_unsupported_type(auth_headers):
    c = TestClient(app)
    r = c.post("/contracts/analyze", headers=auth_headers,
               files={"old_file": ("a.exe", b"x"), "new_file": ("b.txt", b"x")})
    assert r.status_code == 400


def test_broken_pdf_gives_clear_422(auth_headers):
    c = TestClient(app)
    r = c.post("/contracts/analyze", headers=auth_headers,
               files={"old_file": ("a.pdf", b"not a real pdf"), "new_file": ("b.txt", NEW)})
    assert r.status_code == 422
    assert "a.pdf" in r.json()["detail"]
