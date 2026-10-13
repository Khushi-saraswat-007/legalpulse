import json
import pathlib

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Analysis, User
from ..services.analysis import analyze_texts
from .auth import get_current_user

router = APIRouter(prefix="/contracts", tags=["contracts"])
MOCK = pathlib.Path(__file__).resolve().parents[3] / "schemas" / "sample_risk_report.json"


async def _read_text(f: UploadFile) -> str:
    raw = await f.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


@router.post("/analyze")
async def analyze(old_file: UploadFile = File(...), new_file: UploadFile = File(...),
                  contract_key: str = Form("c001"), db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    """Upload the OLD and NEW version of a contract (.txt). Returns the risk report and saves it."""
    for f in (old_file, new_file):
        if not (f.filename or "").lower().endswith(".txt"):
            raise HTTPException(400, f"{f.filename}: only .txt files are supported for now")
    old_text, new_text = await _read_text(old_file), await _read_text(new_file)
    try:
        report = analyze_texts(old_text, new_text, contract_key)
    except ValueError as e:
        raise HTTPException(422, str(e))

    row = Analysis(
        owner_id=user.id,
        contract_key=contract_key, old_filename=old_file.filename, new_filename=new_file.filename,
        n_changes=sum(1 for c in report["changes"] if c["change_type"] != "unchanged"),
        n_risks=len(report["risks"]),
        top_severity=report["risks"][0]["severity"] if report["risks"] else "none",
        report_json=json.dumps(report))
    db.add(row)
    db.commit()
    report["analysis_id"] = row.id
    return report


@router.get("")
def list_analyses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Summaries of the logged-in user's analyses, newest first (for the dashboard)."""
    rows = db.scalars(
        select(Analysis).where(Analysis.owner_id == user.id).order_by(Analysis.id.desc())
    ).all()
    return [{"id": r.id, "contract_key": r.contract_key, "old_filename": r.old_filename,
             "new_filename": r.new_filename, "n_changes": r.n_changes, "n_risks": r.n_risks,
             "top_severity": r.top_severity, "created_at": r.created_at.isoformat()} for r in rows]


@router.get("/{analysis_id}")
def get_analysis(analysis_id: int, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    """The full saved report for one of the user's analyses."""
    row = db.get(Analysis, analysis_id)
    if row is None or row.owner_id != user.id:
        raise HTTPException(404, "analysis not found")
    report = json.loads(row.report_json)
    report["analysis_id"] = row.id
    return report


@router.get("/{contract_key}/report")
def get_report(contract_key: str):
    """Mock report (kept so the frontend can still be built without uploading anything)."""
    if not MOCK.exists():
        raise HTTPException(404, "no report")
    return json.loads(MOCK.read_text())