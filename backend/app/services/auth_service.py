"""
Authentication service: password hashing, JWT creation/decoding,
and a FastAPI dependency that resolves the current user from a Bearer token.
"""
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import bcrypt

from app.config import settings
from app.database import get_db
from app.models import User, RefreshToken

logger = logging.getLogger("quickmind.auth")

# ---- Password hashing -------------------------------------------------------
def hash_password(plain: str) -> str:
    pw_bytes = plain.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        pw_bytes = plain.encode("utf-8")[:72]
        hashed_bytes = hashed.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"Error verifying password: {e}", exc_info=True)
        return False

# ---- JWT --------------------------------------------------------------------
_bearer_scheme = HTTPBearer(auto_error=False)

def create_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def _decode_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        sub = payload.get("sub")
        return int(sub) if sub else None
    except JWTError:
        return None

# ---- Refresh tokens ---------------------------------------------------------
REFRESH_TOKEN_EXPIRE_DAYS = 30

def _generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)

def create_refresh_token(user_id: int, db: Session) -> str:
    raw = _generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db_token = RefreshToken(user_id=user_id, token=raw, expires_at=expires_at)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return raw

def validate_refresh_token(raw_token: str, db: Session) -> Optional[User]:
    db_token = db.query(RefreshToken).filter(RefreshToken.token == raw_token).first()
    if not db_token:
        return None
    if db_token.revoked:
        return None
    if db_token.expires_at < datetime.now(timezone.utc):
        return None
    return db.query(User).filter(User.id == db_token.user_id).first()

def revoke_refresh_token(raw_token: str, db: Session) -> None:
    db_token = db.query(RefreshToken).filter(RefreshToken.token == raw_token).first()
    if db_token:
        db_token.revoked = True
        db.commit()

def revoke_all_user_refresh_tokens(user_id: int, db: Session) -> None:
    db.query(RefreshToken).filter(RefreshToken.user_id == user_id).update({"revoked": True})
    db.commit()

# ---- FastAPI dependency -----------------------------------------------------
def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    _unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please log in to use this feature.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise _unauthorized

    user_id = _decode_token(credentials.credentials)
    if user_id is None:
        raise _unauthorized

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise _unauthorized

    return user
