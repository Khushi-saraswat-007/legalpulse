from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="reviewer")  # reviewer | manager


class Contract(Base):
    __tablename__ = "contracts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_key: Mapped[str] = mapped_column(String)          # e.g. "c001"
    version: Mapped[str] = mapped_column(String)                # e.g. "v1"
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    file_path: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="uploaded")  # uploaded|processing|analysed|failed
    clauses_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # nlp_core output
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_key: Mapped[str] = mapped_column(String)
    report_json: Mapped[str] = mapped_column(Text)              # reasoning output
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    contract_key: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(String)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    seen: Mapped[bool] = mapped_column(Boolean, default=False)


class Analysis(Base):
    """One uploaded old/new contract pair and its risk report (this is what the dashboard lists)."""
    __tablename__ = "analyses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_key: Mapped[str] = mapped_column(String)
    old_filename: Mapped[str] = mapped_column(String)
    new_filename: Mapped[str] = mapped_column(String)
    n_changes: Mapped[int] = mapped_column(Integer, default=0)       # changes that are not "unchanged"
    n_risks: Mapped[int] = mapped_column(Integer, default=0)
    top_severity: Mapped[str] = mapped_column(String, default="none")
    report_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)