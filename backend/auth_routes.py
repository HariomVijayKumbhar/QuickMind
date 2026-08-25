from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from database import get_db
from models import User
from security import (
    get_current_user,
    hash_password,
    verify_password,
    create_access_token,
)
from auth_schemas import RegisterRequest, LoginRequest, GoogleAuthRequest, TokenResponse, UserResponse
from utils import limiter, get_client_ip

router = APIRouter(prefix="/api/auth", tags=["auth"])


auth_limiter = limiter.__class__(max_requests=5, window_seconds=60)


def get_or_create_user_by_google(db: Session, google_id: str, email: str) -> User:
    user = db.query(User).filter(User.google_id == google_id).first()
    if user:
        return user
    user = User(email=email, google_id=google_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, request, db: Session = Depends(get_db)):
    client_ip = get_client_ip(request)
    if not auth_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, request, db: Session = Depends(get_db)):
    client_ip = get_client_ip(request)
    if not auth_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not user.hashed_password or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token)


@router.post("/google", response_model=TokenResponse)
def google_auth(req: GoogleAuthRequest, request, db: Session = Depends(get_db)):
    client_ip = get_client_ip(request)
    if not auth_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        id_info = id_token.verify_oauth2_token(
            req.id_token,
            google_requests.Request(),
            os.getenv("GOOGLE_CLIENT_ID"),
        )
        google_id = id_info.get("sub")
        email = id_info.get("email")
        if not google_id or not email:
            raise HTTPException(status_code=400, detail="Invalid Google token")
        user = get_or_create_user_by_google(db, google_id, email)
        token = create_access_token(user.id, user.email)
        return TokenResponse(access_token=token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Google authentication failed: {e}")


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at.isoformat() if current_user.created_at else "",
    )
