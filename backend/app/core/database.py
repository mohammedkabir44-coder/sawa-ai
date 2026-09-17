"""Database engine and session management.

Supports PostgreSQL (e.g. Neon) via DATABASE_URL. Falls back to a clearly
marked local SQLite file for development when no PostgreSQL is available.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# SQLite needs check_same_thread=False for FastAPI's threadpool.
connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

import os
# CRITICAL FIX: Vercel filesystem is read-only. Redirect SQLite to /tmp/
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///./"):
    db_url = db_url.replace("sqlite:///./", "sqlite:////tmp/")
    print("VERCEL FIX: Redirected SQLite to /tmp/ folder!")

engine = create_engine(
    db_url,
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()