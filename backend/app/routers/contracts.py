import json, pathlib
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/contracts", tags=["contracts"])
MOCK = pathlib.Path(__file__).resolve().parents[3] / "schemas" / "sample_risk_report.json"


# TODO: POST /contracts/upload (old + new files), GET /contracts, GET /contracts/{id}
@router.get("/{contract_key}/report")
def get_report(contract_key: str):
    """Serves mock report until the real pipeline is wired in, so the frontend can build now."""
    if not MOCK.exists():
        raise HTTPException(404, "no report")
    return json.loads(MOCK.read_text())
