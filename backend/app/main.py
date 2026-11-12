import os
import logging
logging.basicConfig(level=logging.INFO)
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import Base, engine
from . import models  # noqa: F401  (registers tables)
from .routers import auth, contracts, alerts

Base.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the ML models once at startup; start the monitoring job only when MONITOR_USER_EMAIL is set."""
    if os.getenv("LEGALPULSE_WARMUP", "1") == "1":
        from .services.analysis import warm_up
        warm_up()
    scheduler = None
    if os.getenv("MONITOR_USER_EMAIL"):
        from apscheduler.schedulers.background import BackgroundScheduler
        from .services.monitor import run_job
        scheduler = BackgroundScheduler()
        scheduler.add_job(run_job, "interval", minutes=int(os.getenv("MONITOR_MINUTES", "1")),
                          max_instances=1)
        scheduler.start()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(title="LegalPulse API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:3000"],
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
app.include_router(contracts.router)
app.include_router(alerts.router)


@app.get("/health")
def health():
    return {"status": "ok"}