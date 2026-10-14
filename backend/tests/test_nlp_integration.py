"""nlp_core is wired into the backend: clauses come from Part B, and PDF/DOCX uploads work."""
import io

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.analysis import analyze_texts

OLD = """SERVICES AGREEMENT between Acme Corp (the "Supplier") and Beta Ltd (the "Client").

1. Payment
The Client shall pay the Supplier within 30 days of invoice.

2. Termination
Either party may terminate this Agreement with 60 days written notice. Payment obligations under Clause 1 survive.

3. Liability
The Supplier's liability is capped at the fees paid under Clause 1.
"""
NEW = OLD.replace("30 days", "90 days").replace("60 days", "7 days")


def _docx_bytes(text: str) -> bytes:
    from docx import Document
    d = Document()
    for para in text.split("\n"):
        d.add_paragraph(para)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def test_report_uses_nlp_core_metadata():
    rep = analyze_texts(OLD, NEW, "t9")
    assert rep["meta"]["old_clauses"] == 3 and rep["meta"]["nli"]
    assert "contradictions" in rep["meta"]
    # Clause 2 cites Clause 1, so changing clause 1 must reach clause 2 (the old stand-in splitter missed this)
    first = next(r for r in rep["risks"] if r["trigger_clause"].endswith("_1"))
    assert any(c.endswith("_2") for c in first["impacted_clauses"])


def test_docx_upload_is_accepted(auth_headers):
    c = TestClient(app)
    r = c.post("/contracts/analyze", data={"contract_key": "d1"}, headers=auth_headers,
               files={"old_file": ("old.docx", _docx_bytes(OLD)), "new_file": ("new.docx", _docx_bytes(NEW))})
    assert r.status_code == 200, r.text
    assert r.json()["meta"]["old_clauses"] == 3


def test_mixed_txt_and_docx(auth_headers):
    c = TestClient(app)
    r = c.post("/contracts/analyze", data={"contract_key": "d2"}, headers=auth_headers,
               files={"old_file": ("old.txt", OLD.encode()), "new_file": ("new.docx", _docx_bytes(NEW))})
    assert r.status_code == 200, r.text


def test_old_contract_has_empty_contradictions_and_report_is_marked_experimental():
    from backend.app.services.analysis import _contract_from_text
    old, _ = _contract_from_text(OLD, "t7", "v1", find_contradictions=False)
    assert old["contradictions"] == []              # field present (schema valid), just empty
    assert analyze_texts(OLD, NEW, "t8")["meta"]["contradictions_status"] == "experimental"


def test_warm_up_runs_with_rule_models():
    from backend.app.services.analysis import warm_up
    warm_up()


def test_contract_name_is_cleaned_and_saved(auth_headers):
    c = TestClient(app)
    r = c.post("/contracts/analyze", data={"contract_key": "  Acme / Supply Agreement!! "}, headers=auth_headers,
               files={"old_file": ("o.txt", OLD.encode()), "new_file": ("n.txt", NEW.encode())})
    assert r.status_code == 200, r.text
    names = [x["contract_key"] for x in c.get("/contracts", headers=auth_headers).json()]
    assert "Acme-Supply-Agreement" in names
