"""Sign-up, sign-in and sign-out.

Passwords are hashed with Argon2id (argon2-cffi defaults: 64 MiB, 3 passes, 4 lanes, RFC 9106's recommended
profile). A session is a random 256-bit token; only its SHA-256 is stored, so the database alone cannot be
used to sign in. The web app keeps the token in an httpOnly cookie on its own domain and sends it here as
a Bearer token (apps/web/src/app/api/session/*), so no browser script can read it.
"""
from __future__ import annotations

import hashlib
import re
import secrets
import threading
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from packages.core import telemetry
from packages.database.models import User, UserSession
from packages.database.session import get_session

SESSION_DAYS = 7
MIN_PASSWORD = 12
MAX_PASSWORD = 128          # bounds the hashing work one request can cause
EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$")

_hasher = PasswordHasher()
# Checked against when the email is unknown, so a wrong email takes as long as a wrong password and the
# response time does not reveal which accounts exist.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class Credentials(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(min_length=1, max_length=MAX_PASSWORD)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL.match(v):
            raise ValueError("Enter a valid email address")
        return v


class SignUp(Credentials):
    password: str = Field(min_length=MIN_PASSWORD, max_length=MAX_PASSWORD)


def _issue(session: Session, user: User) -> dict:
    token = secrets.token_urlsafe(32)
    expires = _now() + timedelta(days=SESSION_DAYS)
    session.add(UserSession(user_id=user.id, token_hash=token_hash(token), expires_at=expires))
    session.commit()
    return {"token": token, "expires_at": expires.isoformat(), "user": {"id": user.id, "email": user.email}}


def current_user(authorization: str | None = Header(None),
                 session: Session = Depends(get_session)) -> User:
    """The signed-in user, or 401. Every per-user endpoint depends on this; nothing trusts a user id sent
    by the client."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in to continue.",
                            headers={"WWW-Authenticate": "Bearer"})
    row = session.query(UserSession).filter_by(token_hash=token_hash(authorization[7:].strip())).first()
    if row is None or row.revoked_at is not None or _aware(row.expires_at) <= _now():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your session has ended. Sign in again.",
                            headers={"WWW-Authenticate": "Bearer"})
    user = session.get(User, row.user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in to continue.")
    return user


@router.post("/signup", status_code=201)
def signup(body: SignUp, session: Session = Depends(get_session)) -> dict:
    user = User(email=body.email, password_hash=_hasher.hash(body.password), role="user")
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "An account with this email already exists. Sign in instead.")
    telemetry.track("signup", user.id)
    return _issue(session, user)


# Failed sign-ins per email, in this process: stops password guessing against one account however many
# addresses an attacker uses. Resets on restart (documented in docs/SECURITY_MODEL.md).
MAX_FAILURES, FAILURE_WINDOW = 5, timedelta(minutes=15)
_failures: dict[str, list[datetime]] = {}
_failures_lock = threading.Lock()


def _recent_failures(email: str) -> list[datetime]:
    cutoff = _now() - FAILURE_WINDOW
    with _failures_lock:
        recent = [t for t in _failures.get(email, []) if t > cutoff]
        _failures[email] = recent
        return recent


@router.post("/login")
def login(body: Credentials, session: Session = Depends(get_session)) -> dict:
    if len(_recent_failures(body.email)) >= MAX_FAILURES:
        raise HTTPException(429, "Too many failed sign-ins for this account. Try again in 15 minutes.")
    user = session.query(User).filter_by(email=body.email).first()
    try:
        _hasher.verify(user.password_hash if user else _DUMMY_HASH, body.password)
    except (VerificationError, InvalidHashError):
        user = None
    if user is None:
        with _failures_lock:
            _failures.setdefault(body.email, []).append(_now())
        raise HTTPException(401, "Email or password is incorrect.")
    with _failures_lock:
        _failures.pop(body.email, None)
    if _hasher.check_needs_rehash(user.password_hash):
        user.password_hash = _hasher.hash(body.password)
        session.commit()
    telemetry.track("login", user.id)
    return _issue(session, user)


@router.post("/logout", status_code=204)
def logout(authorization: str | None = Header(None), session: Session = Depends(get_session)) -> None:
    if authorization and authorization.startswith("Bearer "):
        row = session.query(UserSession).filter_by(token_hash=token_hash(authorization[7:].strip())).first()
        if row is not None and row.revoked_at is None:
            row.revoked_at = _now()
            session.commit()


@router.get("/me")
def me(user: User = Depends(current_user)) -> dict:
    return {"id": user.id, "email": user.email}
