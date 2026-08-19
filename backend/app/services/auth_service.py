"""
Authentication service: password hashing, JWT creation/decoding,
and a FastAPI dependency that resolves the current user from a Bearer token.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import bcrypt

from app.config import settings
from app.database import get_db
from app.models import User

logger = logging.getLogger("quickmind.auth")

# ---- Password hashing -------------------------------------------------------
def hash_password(plain: str) -> str:
    # Truncate to 72 bytes to respect bcrypt's hard limit
    pw_bytes = plain.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
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
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def _decode_token(token: str) -> Optional[int]:
    """Return user_id from token, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        sub = payload.get("sub")
        return int(sub) if sub else None
    except JWTError:
        return None

# ---- FastAPI dependency -----------------------------------------------------
def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Resolve the authenticated User from the Authorization: Bearer <token> header.
    Raises HTTP 401 for missing, malformed, or expired tokens.
    """
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
