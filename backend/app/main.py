from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import Base, engine
from . import models  # noqa: F401  (registers tables)
from .routers import auth, contracts, alerts

Base.metadata.create_all(engine)
app = FastAPI(title="LegalPulse API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
app.include_router(contracts.router)
app.include_router(alerts.router)


@app.get("/health")
def health():
    return {"status": "ok"}
