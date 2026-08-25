"""Initialize the database: create tables and seed system roles.

Run from the backend directory:
    python init_db.py

This is safe to run repeatedly — it never drops data.
"""
import sys
from pathlib import Path

# Ensure backend/ is on sys.path so `app` imports work.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.models import *  # noqa: F401,F403  (registers all models on Base.metadata)
from app.models.user import Role


def init_db() -> None:
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    print("Seeding system roles...")
    db = SessionLocal()
    try:
        for name, description in [
            ("owner", "Business owner with full access"),
            ("admin", "Business administrator"),
            ("staff", "Business staff member"),
        ]:
            existing = db.scalar(select(Role).where(Role.name == name))
            if existing is None:
                db.add(Role(name=name, description=description, is_system=True))
                print(f"  + created role '{name}'")
            else:
                print(f"  = role '{name}' already exists")
        db.commit()
    finally:
        db.close()

    print("Database initialized successfully.")


if __name__ == "__main__":
    init_db()