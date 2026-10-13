from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Alert, User
from .auth import get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])

ALERT_SEVERITIES = ("medium", "high", "critical")


def create_risk_alert(db: Session, user_id: int, contract_key: str, report: dict):
    """Called after an analysis is saved. Creates an alert if the top risk is serious enough."""
    risks = report.get("risks", [])
    if not risks or risks[0]["severity"] not in ALERT_SEVERITIES:
        return None
    top = risks[0]
    msg = f"{top['severity'].capitalize()} risk in {contract_key}: {top.get('explanation', '')}"[:300]
    alert = Alert(user_id=user_id, contract_key=contract_key, message=msg)
    db.add(alert)
    db.commit()
    return alert


@router.get("")
def list_alerts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The logged-in user's alerts, unseen first, newest first."""
    rows = db.scalars(
        select(Alert).where(Alert.user_id == user.id).order_by(Alert.seen, Alert.id.desc())
    ).all()
    return [{"id": a.id, "contract_key": a.contract_key, "message": a.message, "seen": a.seen}
            for a in rows]


@router.post("/{alert_id}/seen")
def mark_seen(alert_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    alert = db.get(Alert, alert_id)
    if alert is None or alert.user_id != user.id:
        raise HTTPException(404, "alert not found")
    alert.seen = True
    db.commit()
    return {"id": alert.id, "seen": True}