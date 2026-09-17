"""Database engine and session management for Vercel Serverless."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import settings

# CRITICAL FIX: Vercel filesystem is read-only. Redirect SQLite to /tmp/
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///./"):
    db_url = "sqlite:////tmp/sawa_vercel.db"
    print("VERCEL FIX: Redirected SQLite to /tmp/ folder!")

connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
