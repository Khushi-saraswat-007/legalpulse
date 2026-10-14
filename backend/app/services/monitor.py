"""Continuous monitoring job.

Watches a folder for new contract pairs named <key>_v1.<ext> and <key>_v2.<ext> (.txt, .pdf or .docx).
Each complete pair is analysed, saved for the owner user, and a risk alert is raised.
Handled files move to processed/ (or failed/), so nothing is analysed twice.
"""
import json
import logging
import pathlib
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Analysis, User
from .analysis import ROOT, SUPPORTED_EXTENSIONS, analyze_files

log = logging.getLogger("legalpulse.monitor")
WATCH_DIR = ROOT / "data" / "incoming"
V1 = re.compile(r"^(?P<key>.+)_v1(?P<ext>\.(?:txt|pdf|docx))$", re.IGNORECASE)


def _move(files, folder: pathlib.Path):
    folder.mkdir(exist_ok=True)
    for f in files:
        f.replace(folder / f.name)


def scan_and_process(db: Session, owner_email: str, watch_dir: pathlib.Path = WATCH_DIR) -> list:
    """Analyse every complete v1/v2 pair in watch_dir. Returns the contract keys processed."""
    from ..routers.alerts import create_risk_alert  # imported here to avoid a circular import

    watch_dir = pathlib.Path(watch_dir)
    owner = db.scalar(select(User).where(User.email == owner_email.strip().lower()))
    if owner is None:
        log.warning("monitor: no user with email %s, skipping", owner_email)
        return []
    if not watch_dir.exists():
        return []

    done = []
    for old_path in sorted(watch_dir.iterdir()):
        m = V1.match(old_path.name)
        if not m:
            continue
        key = m.group("key")
        new_path = next((p for p in sorted(watch_dir.glob(f"{key}_v2.*"))
                         if p.suffix.lower() in SUPPORTED_EXTENSIONS), None)
        if new_path is None:
            continue  # wait until the second version arrives
        try:
            report = analyze_files(old_path.name, old_path.read_bytes(), new_path.name,
                                   new_path.read_bytes(), key)
        except Exception as e:  # bad file: park it so it is not retried forever
            log.error("monitor: could not analyse %s: %s", key, e)
            _move([old_path, new_path], watch_dir / "failed")
            continue
        row = Analysis(
            owner_id=owner.id, contract_key=key,
            old_filename=old_path.name, new_filename=new_path.name,
            n_changes=sum(1 for c in report["changes"] if c["change_type"] != "unchanged"),
            n_risks=len(report["risks"]),
            top_severity=report["risks"][0]["severity"] if report["risks"] else "none",
            report_json=json.dumps(report))
        db.add(row)
        db.commit()
        create_risk_alert(db, owner.id, key, report)
        _move([old_path, new_path], watch_dir / "processed")
        done.append(key)
        log.info("monitor: analysed %s", key)
    return done


def run_job():
    """What the scheduler calls: open a DB session, scan, close."""
    import os
    from ..db import SessionLocal

    db = SessionLocal()
    try:
        scan_and_process(db, os.environ["MONITOR_USER_EMAIL"])
    except Exception:
        log.exception("monitor job failed")
    finally:
        db.close()