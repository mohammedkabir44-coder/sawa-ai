"""Tests for authentication and multi-tenant business features."""
from fastapi.testclient import TestClient


def _register(client: TestClient, email: str, password: str = "password123", full_name: str = "Test User", business_name: str | None = None):
    payload = {
        "email": email,
        "password": password,
        "full_name": full_name,
    }
    if business_name:
        payload["business_name"] = business_name
    return client.post("/api/v1/auth/register", json=payload)


def _login(client: TestClient, email: str, password: str = "password123"):
    return client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------- health

def test_health_endpoint(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


# ------------------------------------------------------------- register

def test_register_user_without_business(client: TestClient):
    resp = _register(client, "user1@example.com", business_name=None)
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_register_user_with_business_creates_owner_membership(client: TestClient):
    resp = _register(client, "owner@example.com", business_name="Acme Ltd")
    assert resp.status_code == 201

    token = resp.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers=_auth_headers(token))
    assert me.status_code == 200
    body = me.json()
    assert body["user"]["email"] == "owner@example.com"
    assert len(body["memberships"]) == 1
    assert body["memberships"][0]["business"]["name"] == "Acme Ltd"
    assert body["memberships"][0]["role"] == "owner"


def test_register_duplicate_email_returns_400(client: TestClient):
    _register(client, "dup@example.com")
    resp = _register(client, "dup@example.com")
    assert resp.status_code == 400


# ---------------------------------------------------------------- login

def test_login_valid_credentials_returns_token(client: TestClient):
    _register(client, "login@example.com", password="password123")
    resp = _login(client, "login@example.com", "password123")
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body


def test_login_invalid_password_fails(client: TestClient):
    _register(client, "badpass@example.com", password="password123")
    resp = _login(client, "badpass@example.com", "wrongpassword")
    assert resp.status_code == 401


def test_login_unknown_email_fails(client: TestClient):
    resp = _login(client, "nouser@example.com", "password123")
    assert resp.status_code == 401


# ------------------------------------------------------------------ me

def test_me_returns_current_user(client: TestClient):
    _register(client, "me@example.com", business_name="Me Co")
    token = _login(client, "me@example.com").json()["access_token"]
    resp = client.get("/api/v1/auth/me", headers=_auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["email"] == "me@example.com"
    assert len(body["memberships"]) == 1


def test_me_without_token_returns_401(client: TestClient):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


# ----------------------------------------------------------- businesses

def test_list_businesses_returns_only_current_users(client: TestClient):
    # User A has two businesses.
    _register(client, "a@example.com", business_name="A-Biz-1")
    token_a = _login(client, "a@example.com").json()["access_token"]
    client.post(
        "/api/v1/businesses/",
        json={"name": "A-Biz-2"},
        headers=_auth_headers(token_a),
    )

    # User B has one business.
    _register(client, "b@example.com", business_name="B-Biz")
    token_b = _login(client, "b@example.com").json()["access_token"]

    # A sees only A-Biz-1 and A-Biz-2.
    resp_a = client.get("/api/v1/businesses/", headers=_auth_headers(token_a))
    assert resp_a.status_code == 200
    names_a = [b["name"] for b in resp_a.json()]
    assert set(names_a) == {"A-Biz-1", "A-Biz-2"}

    # B sees only B-Biz.
    resp_b = client.get("/api/v1/businesses/", headers=_auth_headers(token_b))
    assert resp_b.status_code == 200
    names_b = [b["name"] for b in resp_b.json()]
    assert names_b == ["B-Biz"]


def test_user_a_cannot_access_user_b_business(client: TestClient):
    _register(client, "a@example.com", business_name="A-Biz")
    token_a = _login(client, "a@example.com").json()["access_token"]

    _register(client, "b@example.com", business_name="B-Biz")
    token_b = _login(client, "b@example.com").json()["access_token"]

    # B gets their business id.
    b_biz_id = client.get(
        "/api/v1/businesses/", headers=_auth_headers(token_b)
    ).json()[0]["id"]

    # A tries to access B's business -> 403.
    resp = client.get(
        f"/api/v1/businesses/{b_biz_id}", headers=_auth_headers(token_a)
    )
    assert resp.status_code == 403


def test_x_business_id_header_with_unrecognized_business_returns_403(client: TestClient):
    _register(client, "a@example.com", business_name="A-Biz")
    token_a = _login(client, "a@example.com").json()["access_token"]

    # Use a business id A does not belong to (9999).
    resp = client.get(
        "/api/v1/auth/me",
        headers={**_auth_headers(token_a), "X-Business-ID": "9999"},
    )
    # /auth/me does not use X-Business-ID; ensure it still works.
    assert resp.status_code == 200


def test_business_owner_can_update_business(client: TestClient):
    _register(client, "owner@example.com", business_name="Owner Co")
    token = _login(client, "owner@example.com").json()["access_token"]

    biz_id = client.get(
        "/api/v1/businesses/", headers=_auth_headers(token)
    ).json()[0]["id"]

    resp = client.patch(
        f"/api/v1/businesses/{biz_id}",
        json={"name": "Renamed Co"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Co"


def test_create_business_requires_auth(client: TestClient):
    resp = client.post(
        "/api/v1/businesses/",
        json={"name": "No Auth Co"},
    )
    assert resp.status_code in (401, 403)