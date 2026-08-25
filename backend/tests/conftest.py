"""Pytest fixtures using an isolated in-memory SQLite database.

Each test gets a fresh database: tables are dropped and recreated, and the
three system roles (owner, admin, staff) are seeded per test.  This avoids
the session/function fixture mismatch that previously caused flaky state
leakage between tests.
"""
import sys
from pathlib import Path

# Ensure backend/ is on sys.path so `app` imports work.
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from typing import Optional, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.user import Role


# Engine - in-memory SQLite with StaticPool so every connection shares the
# same database. Created once per session and disposed at the end.
@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield engine
    engine.dispose()


# Helpers
def seed_roles(session: Session) -> None:
    """Insert the three system roles if they don't already exist."""
    for name in ("owner", "admin", "staff"):
        existing = session.query(Role).filter(Role.name == name).first()
        if existing is None:
            session.add(Role(name=name, is_system=True))


# Per-test database session
@pytest.fixture()
def db_session(test_engine) -> Generator[Session, None, None]:
    """Provide a fresh, fully-isolated database session per test.

    Tables are dropped and recreated so no data leaks between tests.
    System roles are seeded so auth/tenant code always finds them.
    """
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


# FastAPI test client
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


# Shared helpers for tenant-scoped tests
def register_user(
    client: TestClient,
    email: str,
    password: str = "password123",
    full_name: str = "Test User",
    business_name: Optional[str] = None
) -> object:
    """Register a user (optionally creating a business)."""
    payload = {
        "email": email,
        "password": password,
        "full_name": full_name
    }
    if business_name:
        payload["business_name"] = business_name
    return client.post("/api/v1/auth/register", json=payload)


def login_user(client: TestClient, email: str, password: str = "password123") -> str:
    """Login and return the token."""
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    """Return Authorization header dict."""
    return {"Authorization": f"Bearer {token}"}


def create_business(
    client: TestClient,
    token: str,
    name: str = "Test Biz"
) -> int:
    """Create a business and return its id."""
    resp = client.post(
        "/api/v1/businesses/",
        json={"name": name},
        headers=auth_headers(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def setup_tenant(
    client: TestClient,
    email: str,
    business_name: str = "Test Biz"
) -> tuple[str, int]:
    """Register a user with a business and return (token, business_id)."""
    register_user(client, email, business_name=business_name)
    token = login_user(client, email)
    biz_id = create_business(client, token, business_name)
    return token, biz_id
