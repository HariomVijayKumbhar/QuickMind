"""
Auth routes: signup, login, refresh, logout, get current user.
"""
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, RefreshToken
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_token,
    get_current_user,
    validate_refresh_token,
    revoke_refresh_token,
    revoke_all_user_refresh_tokens,
    create_refresh_token,
)

logger = logging.getLogger("quickmind.auth")
router = APIRouter(prefix="/api/auth", tags=["Auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordStrengthError(Exception):
    pass


def validate_password_strength(password: str) -> None:
    if len(password) < 6:
        raise PasswordStrengthError("Password must be at least 6 characters long.")


_login_attempts: dict[str, tuple[int, datetime]] = {}


def _check_rate_limit(ip: str) -> None:
    now = datetime.now(timezone.utc)
    attempts, first_attempt = _login_attempts.get(ip, (0, now))
    if now - first_attempt > timedelta(minutes=15):
        _login_attempts[ip] = (1, now)
        return
    if attempts >= 5:
        wait = 15 - (now - first_attempt).seconds // 60
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {wait} minutes.",
        )
    _login_attempts[ip] = (attempts + 1, first_attempt)


@router.post("/signup")
def signup(body: SignupRequest, request: Request, db: Session = Depends(get_db)):
    try:
        validate_password_strength(body.password)
    except PasswordStrengthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    user = User(email=body.email, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_token(user.id)
    refresh_token = create_refresh_token(user.id, db)
    logger.info("New user registered: id=%d", user.id)
    return {
        "success": True,
        "token": access_token,
        "refresh_token": refresh_token,
        "email": user.email,
    }


@router.post("/login")
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    _check_rate_limit(ip)

    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        logger.warning("Failed login attempt for email=%s from ip=%s", body.email, ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    access_token = create_token(user.id)
    refresh_token = create_refresh_token(user.id, db)
    _login_attempts.pop(ip, None)
    logger.info("User logged in: id=%d", user.id)
    return {
        "success": True,
        "token": access_token,
        "refresh_token": refresh_token,
        "email": user.email,
    }


@router.post("/refresh")
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    user = validate_refresh_token(body.refresh_token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    access_token = create_token(user.id)
    new_refresh_token = create_refresh_token(user.id, db)
    revoke_refresh_token(body.refresh_token, db)
    return {
        "success": True,
        "token": access_token,
        "refresh_token": new_refresh_token,
        "email": user.email,
    }


@router.post("/logout")
def logout(body: RefreshRequest, db: Session = Depends(get_db)):
    revoke_refresh_token(body.refresh_token, db)
    return {"success": True, "message": "Logged out successfully."}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "member_since": current_user.created_at.isoformat(),
        },
    }
