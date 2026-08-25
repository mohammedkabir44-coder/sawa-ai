"""Pytest fixtures for WhatsApp Commerce Engine tests.

Provides an in-memory SQLite database and a FastAPI test client that are
shared with the parent ``backend/tests/conftest.py`` fixtures.  Tests in
this directory can use either the synchronous ``client`` / ``db_session``
fixtures (re-exported from the parent conftest) or the async ``async_client``
fixture defined here.
"""
import sys
from pathlib import Path

# Ensure backend/ is on sys.path so `app` imports work.
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from typing import Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.user import Role


# ---------------------------------------------------------------------------
# Engine — in-memory SQLite with StaticPool so every connection shares the
# same database.  Created once per session and disposed at the end.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield engine
    engine.dispose()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def seed_roles(session: Session) -> None:
    """Insert the three system roles if they don't already exist."""
    for name in ("owner", "admin", "staff"):
        existing = session.query(Role).filter(Role.name == name).first()
        if existing is None:
            session.add(Role(name=name, is_system=True))
    session.commit()


# ---------------------------------------------------------------------------
# Per-test database session
# ---------------------------------------------------------------------------
@pytest.fixture()
def db_session(test_engine) -> Generator[Session, None, None]:
    """Provide a fresh, fully-isolated database session per test."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestingSessionLocal()

    seed_roles(session)
    session.commit()

    yield session

    session.close()


# Alias so tests that use ``db`` fixture name work too.
@pytest.fixture()
def db(db_session: Session) -> Generator[Session, None, None]:
    """Alias for db_session — provides a synchronous SQLAlchemy session."""
    yield db_session


# ---------------------------------------------------------------------------
# FastAPI test client (synchronous)
# ---------------------------------------------------------------------------
@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI test client backed by the per-test db_session."""

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Async test client (for async endpoint tests)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture()
async def async_client(db_session: Session) -> Generator[AsyncClient, None, None]:
    """Async FastAPI test client backed by the per-test db_session."""

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()
