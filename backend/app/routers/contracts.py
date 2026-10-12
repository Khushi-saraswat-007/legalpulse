import json
import pathlib

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..services.analysis import analyze_texts

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
                  contract_key: str = Form("c001")):
    """Upload the OLD and NEW version of a contract (.txt) and get the risk report back."""
    for f in (old_file, new_file):
        if not (f.filename or "").lower().endswith(".txt"):
            raise HTTPException(400, f"{f.filename}: only .txt files are supported for now")
    old_text, new_text = await _read_text(old_file), await _read_text(new_file)
    try:
        return analyze_texts(old_text, new_text, contract_key)
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/{contract_key}/report")
def get_report(contract_key: str):
    """Mock report (kept so the frontend can still be built without uploading anything)."""
    if not MOCK.exists():
        raise HTTPException(404, "no report")
    return json.loads(MOCK.read_text())