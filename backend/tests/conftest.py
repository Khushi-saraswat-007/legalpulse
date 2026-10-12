import os
import sys
import pathlib

os.environ["LEGALPULSE_EMBEDDER"] = "bow"          # fast, no model download in tests
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.db import Base, get_db


@pytest.fixture(autouse=True)
def test_db():
    """Every test gets a fresh in-memory database, so tests never touch legalpulse.db."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    yield
    app.dependency_overrides.clear()