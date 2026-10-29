import hashlib
import logging
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import PasswordReset, User

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-me")
ALGORITHM = "HS256"
TOKEN_MINUTES = 60 * 24
RESET_MINUTES = int(os.getenv("RESET_TOKEN_MINUTES", "30"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
logger = logging.getLogger("legalpulse.auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class RegisterIn(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=72)

class ForgotIn(BaseModel):
    email: str

class ResetIn(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=72)
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_token(user: User) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_MINUTES)
    return jwt.encode({"sub": str(user.id), "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    err = HTTPException(401, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise err
    user = db.get(User, user_id)
    if user is None:
        raise err
    return user


@router.get("/ping")
def ping():
    return {"auth": "ok"}


@router.post("/register", status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "email already registered")
    user = User(email=email, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    return {"id": user.id, "email": user.email, "role": user.role}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username.strip().lower()))
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "wrong email or password")
    return {"access_token": create_token(user), "token_type": "bearer"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "role": user.role}

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def send_reset_email(to_email: str, link: str) -> None:
    """Email the reset link by SMTP if SMTP_HOST is set; otherwise print it in the server log (dev mode)."""
    host = os.getenv("SMTP_HOST")
    if not host:
        logger.warning("PASSWORD RESET LINK for %s: %s", to_email, link)
        return
    msg = EmailMessage()
    msg["Subject"] = "Reset your LegalPulse password"
    msg["From"] = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "no-reply@legalpulse.local"))
    msg["To"] = to_email
    msg.set_content(
        f"Open this link to choose a new password (valid for {RESET_MINUTES} minutes):\n\n{link}\n\n"
        "If you did not ask for this, you can ignore this email."
    )
    with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=15) as server:
        server.starttls()
        server.login(os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", ""))
        server.send_message(msg)


@router.post("/forgot-password")
def forgot_password(body: ForgotIn, db: Session = Depends(get_db)):
    """Always answers the same way, so nobody can find out which emails are registered."""
    generic = {"message": "If that email is registered, a reset link has been sent."}
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if user is None:
        return generic
    token = secrets.token_urlsafe(32)
    db.add(PasswordReset(user_id=user.id, token_hash=_hash_token(token),
                         expires_at=datetime.utcnow() + timedelta(minutes=RESET_MINUTES)))
    db.commit()
    try:
        send_reset_email(user.email, f"{FRONTEND_URL}/reset-password?token={token}")
    except Exception:
        logger.exception("could not send the password reset email")
    return generic


@router.post("/reset-password")
def reset_password(body: ResetIn, db: Session = Depends(get_db)):
    """Set a new password using the token from the reset link (one use, expires)."""
    row = db.scalar(select(PasswordReset).where(PasswordReset.token_hash == _hash_token(body.token)))
    if row is None or row.used or row.expires_at < datetime.utcnow():
        raise HTTPException(400, "This reset link is invalid or has expired.")
    user = db.get(User, row.user_id)
    user.password_hash = hash_password(body.password)
    # use up this link and any other open links of the same user
    for r in db.scalars(select(PasswordReset).where(PasswordReset.user_id == row.user_id,
                                                    PasswordReset.used.is_(False))):
        r.used = True
    db.commit()
    return {"message": "Password updated. You can log in now."}