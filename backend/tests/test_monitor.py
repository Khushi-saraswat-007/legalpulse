from fastapi.testclient import TestClient

from backend.app.db import get_db
from backend.app.main import app
from backend.app.services.monitor import scan_and_process

OLD = b"""AGREEMENT

1. Payment. Buyer shall pay each invoice within 30 days of the invoice date.

2. Late Payment. If Buyer fails to pay under Section 1, interest of 2% per month applies.

3. Termination. Either party may terminate this agreement on 30 days notice. Section 2 survives termination.

4. Governing Law. This agreement is governed by the laws of India and the parties submit to its courts.
"""
NEW = OLD.replace(b"within 30 days", b"within 60 days")


def test_monitor_processes_new_pairs(auth_headers, tmp_path):
    c = TestClient(app)
    db = next(app.dependency_overrides[get_db]())
    (tmp_path / "c010_v1.txt").write_bytes(OLD)
    (tmp_path / "c010_v2.txt").write_bytes(NEW)
    (tmp_path / "c011_v1.txt").write_bytes(OLD)          # no v2 yet: must be left alone

    assert scan_and_process(db, "user1@test.com", tmp_path) == ["c010"]
    assert len(c.get("/contracts", headers=auth_headers).json()) == 1
    assert (tmp_path / "processed" / "c010_v2.txt").exists()
    assert (tmp_path / "c011_v1.txt").exists()

    assert scan_and_process(db, "user1@test.com", tmp_path) == []   # nothing analysed twice
    assert scan_and_process(db, "nobody@test.com", tmp_path) == []  # unknown owner is skipped
    db.close()