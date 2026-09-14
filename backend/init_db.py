"""Initialize the database: create tables and seed system roles.

Run from the backend directory:
    python init_db.py

This is safe to run repeatedly — it never drops data.
Incremental schema changes that can't be expressed with
``Base.metadata.create_all`` (because the table already exists) are applied
here as idempotent ``ALTER TABLE`` statements.
"""
import sys
from pathlib import Path

# Ensure backend/ is on sys.path so `app` imports work.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import inspect, select, text

from app.core.database import Base, SessionLocal, engine
from app.models import *  # noqa: F401,F403  (registers all models on Base.metadata)
from app.models.user import Role

# Incremental columns added after the tables were first created. Each entry is
# ``(table, column, column_type)``; entries are applied only when the column is
# missing, so this is safe to run against existing databases on every deploy.
_INC_COLUMNS = [
    (
        "whatsapp_messages",
        "provider_message_id",
        "VARCHAR(255) NOT NULL DEFAULT ''",
    ),
    (
        "whatsapp_campaigns",
        "message_text",
        "TEXT NOT NULL DEFAULT ''",
    ),
    (
        "whatsapp_campaigns",
        "variables_map",
        "TEXT",
    ),
]


def _ensure_incremental_columns() -> None:
    """Add columns that are missing from existing tables (idempotent)."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    for table, column, column_type in _INC_COLUMNS:
        if table not in existing_tables:
            continue
        columns = {c["name"] for c in inspector.get_columns(table)}
        if column in columns:
            continue
        print(f"  + adding column {table}.{column}")
        with engine.begin() as conn:
            conn.execute(
                text(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {column_type}')
            )


def init_db() -> None:
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    _ensure_incremental_columns()

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