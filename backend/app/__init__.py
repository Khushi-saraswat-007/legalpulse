"""LegalPulse backend package."""
from pathlib import Path

from dotenv import load_dotenv

# Load settings (SMTP_*, JWT_SECRET, ...) from the repo-root .env file, if there is one,
# so the server can be started with a plain `uvicorn backend.app.main:app --reload`.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")