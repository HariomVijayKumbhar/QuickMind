import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlparse, urlencode, parse_qsl

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./quickmind.db") or "sqlite:///./quickmind.db"


VALID_SSLMODES = {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}


def _prepare_postgres_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("postgresql", "postgres"):
        return url
    query = dict(parse_qsl(parsed.query))
    sslmode = query.get("sslmode", "").strip().lower()
    if sslmode not in VALID_SSLMODES:
        query["sslmode"] = "require"
    else:
        query["sslmode"] = sslmode
    if parsed.scheme == "postgres":
        parsed = parsed._replace(scheme="postgresql")
    new_query = urlencode(query)
    return parsed._replace(query=new_query).geturl()


PREPARED_DATABASE_URL = _prepare_postgres_url(DATABASE_URL)

if PREPARED_DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        PREPARED_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
    )
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
