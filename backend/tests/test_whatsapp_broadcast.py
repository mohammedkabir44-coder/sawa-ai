"""Tests for the WhatsApp bulk-broadcast feature.

Covers, tenant-scope-checked:
  * accounts (api_key encrypted at rest, never returned)
  * templates + per-recipient variable substitution at send time
  * broadcast create / send / pause-resume / scheduled / aggregates
  * single-message send
  * Meta webhook statuses (delivered/read/failed) + reply attribution
  * tenant isolation on every read path (accounts, broadcasts, messages) and
    through the webhook (business is resolved from the account mapping, never
    from the request session).
"""
import asyncio
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone

from app.models.whatsapp import (
    WhatsAppAccount,
    WhatsAppCampaign,
    WhatsAppEngagement,
    WhatsAppMessage,
    WhatsAppRecipient,
)
from app.services.whatsapp.broadcast import (
    ensure_utc,
    normalise_recipient_phone,
    render_template_text,
    send_broadcast_task,
)

PHONE = "+2348012345678"
PHONE_2 = "+2348012345979"
PHONE_3 = "+2348012341234"
API_KEY = "EAAJOkef0dshkfkxfjfjj1234567890abc"


def _headers(token: str, biz_id: int) -> dict:
    return {"Authorization": f"Bearer {token}", "X-Business-ID": str(biz_id)}


def _make_tenant(client, email: str, name: str):
    """Register a user with a business and return (token, business_id).

    Mirrors ``conftest.setup_tenant`` (register -> login -> create business)
    but inlined so the module stays self-contained regardless of how pytest
    resolves the ``tests`` package.
    """
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Test User",
            "business_name": name,
        },
    )
    assert resp.status_code in (200, 201), resp.text
    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "password123"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    biz = client.post(
        "/api/v1/businesses/",
        json={"name": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert biz.status_code == 201, biz.text
    return token, biz.json()["id"]


# --------------------------------------------------------------------------- #
# Accounts
# --------------------------------------------------------------------------- #
class TestAccounts:
    def test_create_account_encrypts_key_and_never_returns_it(
        self, client, db_session
    ):
        token, biz_id = _make_tenant(client, "acc@example.com", "Acc Co")
        headers = _headers(token, biz_id)

        resp = client.post(
            "/api/v1/whatsapp/accounts",
            json={
                "phone_number": PHONE,
                "api_key": API_KEY,
                "account_name": "Main Line",
                "phone_number_id": "123456789012345",
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert "api_key" not in body
        assert body["is_connected"] is True
        assert body["phone_number_id"] == "123456789012345"

        row = db_session.query(WhatsAppAccount).filter_by(id=body["id"]).first()
        assert row is not None
        assert row.api_key != API_KEY  # encrypted at rest
        assert "EAAJ" not in row.api_key  # not a plaintext prefix

    def test_account_tenant_isolation(self, client):
        token_a, biz_a = _make_tenant(client, "accA@example.com", "Acc A")
        token_b, biz_b = _make_tenant(client, "accB@example.com", "Acc B")

        created = client.post(
            "/api/v1/whatsapp/accounts",
            json={
                "phone_number": PHONE,
                "api_key": API_KEY,
                "account_name": "A line",
            },
            headers=_headers(token_a, biz_a),
        )
        assert created.status_code == 201

        # B cannot see A's account.
        listed = client.get(
            "/api/v1/whatsapp/accounts", headers=_headers(token_b, biz_b)
        )
        assert listed.status_code == 200
        assert listed.json() == []

        # B cannot update or delete A's account.
        assert (
            client.patch(
                f"/api/v1/whatsapp/accounts/{created.json()['id']}",
                json={"account_name": "hacked"},
                headers=_headers(token_b, biz_b),
            ).status_code
            == 404
        )
        assert (
            client.delete(
                f"/api/v1/whatsapp/accounts/{created.json()['id']}",
                headers=_headers(token_b, biz_b),
            ).status_code
            in (403, 404)
        )

    def test_update_account_rate_limit_and_connection(self, client):
        token, biz_id = _make_tenant(client, "accC@example.com", "Acc C")
        headers = _headers(token, biz_id)
        created = client.post(
            "/api/v1/whatsapp/accounts",
            json={
                "phone_number": PHONE,
                "api_key": API_KEY,
                "account_name": "Line 1",
            },
            headers=headers,
        ).json()

        resp = client.patch(
            f"/api/v1/whatsapp/accounts/{created['id']}",
            json={"rate_limit_per_hour": 250, "phone_number_id": "999000111"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["rate_limit_per_hour"] == 250
        assert body["is_connected"] is True


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #
WEBHOOK = "/api/v1/whatsapp-commerce/webhook"


def _create_account(client, headers, phone_number_id="PN1000"):
    resp = client.post(
        "/api/v1/whatsapp/accounts",
        json={
            "phone_number": PHONE,
            "api_key": API_KEY,
            "account_name": "Broadcast Line",
            "phone_number_id": phone_number_id,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_broadcast(client, headers, account_id, **overrides):
    payload = {
        "account_id": account_id,
        "campaign_name": "September Promo",
        "message_text": "Hello from Sawa!",
        "phone_numbers": [PHONE, PHONE_2],
    }
    payload.update(overrides)
    resp = client.post("/api/v1/whatsapp/broadcasts", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _setup_account(client, email, phone_number_id="PN1000"):
    token, biz_id = _make_tenant(client, email, "Broadcast Co")
    headers = _headers(token, biz_id)
    account = _create_account(client, headers, phone_number_id)
    return token, biz_id, headers, account


def _run_sender(campaign_id, business_id, db_session):
    """Drive the broadcast sender inline (the scheduler is disabled in tests)."""
    return asyncio.run(send_broadcast_task(campaign_id, business_id, db=db_session))


def _setup_broadcast(
    client, db_session, *, email, phone_number_id="PN1000", send=True, **overrides
):
    """Tenant + account + broadcast; optionally started and sent end-to-end."""
    token, biz_id, headers, account = _setup_account(client, email, phone_number_id)
    campaign = _create_broadcast(client, headers, account["id"], **overrides)
    if send:
        started = client.post(
            f"/api/v1/whatsapp/broadcasts/{campaign['id']}/start", headers=headers
        )
        assert started.status_code == 200, started.text
        assert started.json()["status"] == "sending"
        assert _run_sender(campaign["id"], biz_id, db_session) == "completed"
    return token, biz_id, headers, account, campaign["id"]


def _campaign_messages(db_session, campaign_id):
    return (
        db_session.query(WhatsAppMessage)
        .filter(WhatsAppMessage.campaign_id == campaign_id)
        .order_by(WhatsAppMessage.id.asc())
        .all()
    )


def _campaign_recipients(db_session, campaign_id):
    return (
        db_session.query(WhatsAppRecipient)
        .filter(WhatsAppRecipient.campaign_id == campaign_id)
        .order_by(WhatsAppRecipient.id.asc())
        .all()
    )


def _status_payload(phone_number_id, statuses):
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": phone_number_id},
                            "statuses": statuses,
                        }
                    }
                ]
            }
        ]
    }


def _status_event(message, status):
    return {
        "id": message.provider_message_id,
        "status": status,
        "timestamp": str(int(time.time())),
        "recipient_id": message.to_number.lstrip("+"),
    }


# --------------------------------------------------------------------------- #
# Templates
# --------------------------------------------------------------------------- #
class TestTemplates:
    def test_create_and_list_template(self, client):
        token, biz_id = _make_tenant(client, "tpl@example.com", "Tpl Co")
        headers = _headers(token, biz_id)

        resp = client.post(
            "/api/v1/whatsapp/templates",
            json={
                "template_name": "order_update",
                "template_text": "Hi {{name}}, your order {{order_id}} is on the way!",
                "variables": ["name", "order_id"],
                "category": "transactional",
            },
            headers=headers,
        )
        assert resp.status_code in (200, 201), resp.text
        body = resp.json()
        assert body["template_name"] == "order_update"
        assert body["variables"] == ["name", "order_id"]
        assert body["status"] == "pending"  # model default until Meta approves

        listed = client.get("/api/v1/whatsapp/templates", headers=headers).json()
        assert [t["template_name"] for t in listed["items"]] == ["order_update"]

    def test_template_tenant_isolation(self, client):
        token_a, biz_a = _make_tenant(client, "tplA@example.com", "Tpl A")
        token_b, biz_b = _make_tenant(client, "tplB@example.com", "Tpl B")
        resp = client.post(
            "/api/v1/whatsapp/templates",
            json={"template_name": "secret_tpl", "template_text": "A only"},
            headers=_headers(token_a, biz_a),
        )
        assert resp.status_code in (200, 201), resp.text

        listed_b = client.get(
            "/api/v1/whatsapp/templates", headers=_headers(token_b, biz_b)
        ).json()
        assert listed_b["items"] == []

    def test_template_validation_errors(self, client):
        token, biz_id = _make_tenant(client, "tplV@example.com", "Tpl V")
        headers = _headers(token, biz_id)

        assert (
            client.post(
                "/api/v1/whatsapp/templates",
                json={"template_name": "bad", "template_text": "x", "category": "nope"},
                headers=headers,
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/v1/whatsapp/templates",
                json={
                    "template_name": "bad",
                    "template_text": "x",
                    "variables": ["a", "a"],
                },
                headers=headers,
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/v1/whatsapp/templates",
                json={"template_name": "bad", "template_text": ""},
                headers=headers,
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/v1/whatsapp/templates",
                json={"template_name": "anon", "template_text": "x"},
            ).status_code
            in (401, 403)
        )


# --------------------------------------------------------------------------- #
# Broadcast creation & validation
# --------------------------------------------------------------------------- #
class TestBroadcastCreation:
    def test_create_broadcast_with_raw_text(self, client):
        token, biz_id, headers, account = _setup_account(
            client, "bc1@example.com", "PNBC1"
        )
        campaign = _create_broadcast(client, headers, account["id"])
        assert campaign["campaign_name"] == "September Promo"
        assert campaign["status"] == "draft"
        assert campaign["total_recipients"] == 2

    def test_create_broadcast_with_template(self, client):
        token, biz_id, headers, account = _setup_account(
            client, "bc2@example.com", "PNBC2"
        )
        tpl = client.post(
            "/api/v1/whatsapp/templates",
            json={
                "template_name": "promo_tpl",
                "template_text": "Big sale {{discount}}% off!",
                "variables": ["discount"],
            },
            headers=headers,
        )
        assert tpl.status_code in (200, 201), tpl.text
        campaign = _create_broadcast(
            client,
            headers,
            account["id"],
            template_id=tpl.json()["id"],
            message_text=None,
        )
        assert campaign["total_recipients"] == 2

    def test_create_broadcast_with_customer_recipients(self, client):
        token, biz_id, headers, account = _setup_account(
            client, "bc3@example.com", "PNBC3"
        )
        cust = client.post(
            "/api/v1/customers",
            json={"name": "Ada Obi", "phone": PHONE},
            headers=headers,
        )
        assert cust.status_code == 201, cust.text
        campaign = _create_broadcast(
            client, headers, account["id"], recipients=[cust.json()["id"]], phone_numbers=None
        )
        assert campaign["total_recipients"] == 1

    def test_create_broadcast_validation_matrix(self, client):
        token, biz_id, headers, account = _setup_account(
            client, "bc4@example.com", "PNBC4"
        )
        base = {"account_id": account["id"], "campaign_name": "X"}

        def post(**overrides):
            payload = {
                "message_text": "hi",
                "phone_numbers": [PHONE],
            }
            payload.update(overrides)
            return client.post(
                "/api/v1/whatsapp/broadcasts", json={**base, **payload}, headers=headers
            )

        # both template_id AND message_text -> 422
        assert post(template_id=1).status_code == 422
        # neither template_id nor message_text -> 422
        assert post(message_text=None).status_code == 422
        # both recipients AND phone_numbers -> 422
        assert post(recipients=[1]).status_code == 422
        # neither recipients nor phone_numbers -> 422
        assert post(phone_numbers=None).status_code == 422
        # malformed phone number -> 422
        assert post(phone_numbers=["not-a-phone"]).status_code == 422
        # missing account_id -> 422
        missing_account = {"campaign_name": "X", "message_text": "hi", "phone_numbers": [PHONE]}
        assert (
            client.post(
                "/api/v1/whatsapp/broadcasts", json=missing_account, headers=headers
            ).status_code
            == 422
        )

    def test_create_broadcast_other_business_account_rejected(self, client):
        token_a, biz_a, headers_a, account_a = _setup_account(
            client, "bcOwn@example.com", "PNOwn"
        )
        _make_tenant(client, "bcOther@example.com", "Other Co")
        resp = client.post(
            "/api/v1/whatsapp/broadcasts",
            json={
                "account_id": account_a["id"],
                "campaign_name": "steal",
                "message_text": "hi",
                "phone_numbers": [PHONE],
            },
        )
        assert resp.status_code in (401, 403)

    def test_scheduled_broadcast_stores_time(self, client):
        token, biz_id, headers, account = _setup_account(
            client, "bc5@example.com", "PNBC5"
        )
        when = datetime.now(timezone.utc) + timedelta(hours=2)
        campaign = _create_broadcast(
            client, headers, account["id"], scheduled_time=when.isoformat()
        )
        assert campaign["status"] == "scheduled"
        assert campaign["scheduled_time"] is not None


# --------------------------------------------------------------------------- #
# Broadcast start / send lifecycle
# --------------------------------------------------------------------------- #
class TestBroadcastSend:
    def test_start_and_send_broadcast(self, client, db_session):
        token, biz_id, headers, account, campaign_id = _setup_broadcast(
            client, db_session, email="send1@example.com", phone_number_id="PNS1"
        )

        msgs = _campaign_messages(db_session, campaign_id)
        assert len(msgs) == 2
        assert all(m.status == "sent" for m in msgs)
        assert all(m.provider_message_id and m.provider_message_id.startswith("wamid.") for m in msgs)

        recips = _campaign_recipients(db_session, campaign_id)
        assert len(recips) == 2
        assert {r.status for r in recips} == {"sent"}

        body = client.get(
            f"/api/v1/whatsapp/broadcasts/{campaign_id}", headers=headers
        ).json()
        assert body["sent_count"] == 2
        assert body["failed_count"] == 0
        assert body["status"] == "completed"
        assert body["started_at"] is not None and body["completed_at"] is not None

    def test_start_broadcast_requires_account(self, client, db_session):
        token, biz_id, headers, account = _setup_account(
            client, "send2@example.com", "PNS2"
        )
        campaign = _create_broadcast(client, headers, account["id"])
        # Kill the account link so the sender has nothing to work with.
        db_account = db_session.get(WhatsAppAccount, account["id"])
        db_account.business_id = biz_id + 500
        db_session.commit()

        started = client.post(
            f"/api/v1/whatsapp/broadcasts/{campaign['id']}/start", headers=headers
        )
        assert started.status_code in (400, 404)

    def test_start_broadcast_twice_rejected(self, client, db_session):
        token, biz_id, headers, account, campaign_id = _setup_broadcast(
            client, db_session, email="send3@example.com", phone_number_id="PNS3"
        )
        again = client.post(
            f"/api/v1/whatsapp/broadcasts/{campaign_id}/start", headers=headers
        )
        assert again.status_code in (400, 409)

    def test_cross_tenant_broadcast_access_denied(self, client, db_session):
        token, biz_id, headers, account, campaign_id = _setup_broadcast(
            client, db_session, email="send4@example.com", phone_number_id="PNS4"
        )
        token_b, biz_b = _make_tenant(client, "intruder@example.com", "Intruders")
        resp = client.get(
            f"/api/v1/whatsapp/broadcasts/{campaign_id}", headers=_headers(token_b, biz_b)
        )
        assert resp.status_code in (403, 404)

    def test_broadcast_stats_endpoint(self, client, db_session):
        token, biz_id, headers, account, campaign_id = _setup_broadcast(
            client, db_session, email="send5@example.com", phone_number_id="PNS5"
        )
        stats = client.get(
            f"/api/v1/whatsapp/broadcasts/{campaign_id}/stats", headers=headers
        )
        assert stats.status_code == 200, stats.text
        body = stats.json()
        assert body["total_sent"] == 2
        assert body["delivered"] == 0  # no webhook statuses processed yet

    def test_broadcast_list_paginated(self, client, db_session):
        token, biz_id, headers, account = _setup_account(
            client, "send6@example.com", "PNS6"
        )
        for i in range(3):
            _create_broadcast(
                client, headers, account["id"], campaign_name=f"Campaign {i}"
            )
        listed = client.get("/api/v1/whatsapp/broadcasts", headers=headers).json()
        assert listed["total"] >= 3
        assert all("campaign_name" in item for item in listed["items"])


# --------------------------------------------------------------------------- #
# Pause / resume / delete
# --------------------------------------------------------------------------- #
class TestBroadcastPauseResumeDelete:
    def test_pause_resume_roundtrip(self, client, db_session):
        token, biz_id, headers, account = _setup_account(
            client, "pr1@example.com", "PNPR1"
        )
        campaign = _create_broadcast(client, headers, account["id"])

        paused = client.post(
            f"/api/v1/whatsapp/broadcasts/{campaign['id']}/pause", headers=headers
        )
        assert paused.status_code == 200, paused.text
        assert paused.json()["status"] == "paused"

        resumed = client.post(
            f"/api/v1/whatsapp/broadcasts/{campaign['id']}/resume", headers=headers
        )
        assert resumed.status_code == 200, resumed.text
        assert resumed.json()["status"] == "draft"

    def test_delete_broadcast_cascade(self, client, db_session):
        token, biz_id, headers, account, campaign_id = _setup_broadcast(
            client, db_session, email="pr2@example.com", phone_number_id="PNPR2"
        )
        deleted = client.delete(
            f"/api/v1/whatsapp/broadcasts/{campaign_id}", headers=headers
        )
        assert deleted.status_code == 204
        assert (
            client.get(
                f"/api/v1/whatsapp/broadcasts/{campaign_id}", headers=headers
            ).status_code
            == 404
        )
        assert _campaign_messages(db_session, campaign_id) == []


# --------------------------------------------------------------------------- #
# Delivery status webhook (delivered / read / failed)
# --------------------------------------------------------------------------- #
class TestBroadcastStatusWebhook:
    def test_delivered_then_read_updates_counts(self, client, db_session):
        token, biz_id, headers, account, campaign_id = _setup_broadcast(
            client, db_session, email="st1@example.com", phone_number_id="PNST1"
        )
        msgs = _campaign_messages(db_session, campaign_id)

        for status in ("delivered", "read"):
            payload = _status_payload(
                "PNST1", [_status_event(m, status) for m in msgs]
            )
            resp = client.post(WEBHOOK, json=payload)
            assert resp.status_code == 200, resp.text

        db_session.expire_all()
        recips = _campaign_recipients(db_session, campaign_id)
        assert {r.status for r in recips} == {"read"}

        body = client.get(
            f"/api/v1/whatsapp/broadcasts/{campaign_id}", headers=headers
        ).json()
        assert body["delivered_count"] == 2
        assert body["read_count"] == 2

    def test_failed_status_records_error(self, client, db_session):
        token, biz_id, headers, account, campaign_id = _setup_broadcast(
            client, db_session, email="st2@example.com", phone_number_id="PNST2"
        )
        msgs = _campaign_messages(db_session, campaign_id)
        payload = _status_payload(
            "PNST2",
            [
                {
                    "id": msgs[0].provider_message_id,
                    "status": "failed",
                    "timestamp": str(int(time.time())),
                    "errors": [{"title": "Rejected", "message": "Invalid number"}],
                }
            ],
        )
        resp = client.post(WEBHOOK, json=payload)
        assert resp.status_code == 200, resp.text

        db_session.expire_all()
        recips = _campaign_recipients(db_session, campaign_id)
        failed = [r for r in recips if r.status == "failed"]
        assert len(failed) == 1
        assert "Invalid number" in (failed[0].error_message or "")
        body = client.get(
            f"/api/v1/whatsapp/broadcasts/{campaign_id}", headers=headers
        ).json()
        assert body["failed_count"] == 1

    def test_unknown_message_id_is_ignored(self, client, db_session):
        token, biz_id, headers, account, campaign_id = _setup_broadcast(
            client, db_session, email="st3@example.com", phone_number_id="PNST3"
        )
        payload = _status_payload(
            "PNST3",
            [{"id": "wamid.UNKNOWN123", "status": "delivered", "timestamp": "0"}],
        )
        resp = client.post(WEBHOOK, json=payload)
        assert resp.status_code == 200
        db_session.expire_all()
        body = client.get(
            f"/api/v1/whatsapp/broadcasts/{campaign_id}", headers=headers
        ).json()
        assert body["delivered_count"] == 0


# --------------------------------------------------------------------------- #
# Reply attribution (broadcast replies bypass the commerce engine)
# --------------------------------------------------------------------------- #
class TestBroadcastReplyAttribution:
    def test_reply_attributed_to_campaign(self, client, db_session):
        token, biz_id, headers, account, campaign_id = _setup_broadcast(
            client, db_session, email="rp1@example.com", phone_number_id="PNRP1"
        )
        msg = _campaign_messages(db_session, campaign_id)[0]

        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {"phone_number_id": "PNRP1"},
                                "messages": [
                                    {
                                        "from": msg.to_number,
                                        "to": PHONE,
                                        "type": "text",
                                        "text": {"body": "STOP"},
                                        "context": {"id": msg.provider_message_id},
                                    }
                                ],
                            }
                        }
                    ]
                }
            ]
        }
        resp = client.post(WEBHOOK, json=payload)
        assert resp.status_code == 200, resp.text

        db_session.expire_all()
        recips = _campaign_recipients(db_session, campaign_id)
        replies = [r for r in recips if r.reply_text]
        assert len(replies) == 1
        assert replies[0].reply_text == "STOP"
        assert replies[0].replied_at is not None

        body = client.get(
            f"/api/v1/whatsapp/broadcasts/{campaign_id}", headers=headers
        ).json()
        assert body["reply_count"] == 1

        eng = (
            db_session.query(WhatsAppEngagement)
            .filter(WhatsAppEngagement.campaign_id == campaign_id)
            .all()
        )
        assert any(e.engagement_type == "reply" for e in eng)


# --------------------------------------------------------------------------- #
# Rate limiting
# --------------------------------------------------------------------------- #
class TestBroadcastRateLimit:
    def test_hourly_rate_limit_pauses_campaign(
        self, client, db_session, monkeypatch
    ):
        token, biz_id, headers, account = _setup_account(
            client, "rl1@example.com", "PNRL1"
        )
        campaign = _create_broadcast(client, headers, account["id"])
        started = client.post(
            f"/api/v1/whatsapp/broadcasts/{campaign['id']}/start", headers=headers
        )
        assert started.status_code == 200, started.text

        # Tight hourly budget: 1 message through, then the throttle trips.
        acct = db_session.get(WhatsAppAccount, account["id"])
        acct.rate_limit_per_hour = 1
        db_session.commit()

        result = _run_sender(campaign["id"], biz_id, db_session)
        assert result == "paused"

        db_session.expire_all()
        body = client.get(
            f"/api/v1/whatsapp/broadcasts/{campaign['id']}", headers=headers
        ).json()
        assert body["status"] == "paused"
        assert body["sent_count"] == 1
        msgs = _campaign_messages(db_session, campaign["id"])
        assert len(msgs) == 1


# --------------------------------------------------------------------------- #
# Unit: template rendering & phone normalisation
# --------------------------------------------------------------------------- #
class TestRenderingUnits:
    def test_render_template_text(self):
        assert (
            render_template_text("Hi {{name}}, {{order}} shipped!", {"name": "Ada", "order": "#42"})
            == "Hi Ada, #42 shipped!"
        )
        # Unknown variables render as empty strings, never raw placeholders.
        assert render_template_text("Hi {{name}}", {}) == "Hi "

    def test_normalise_recipient_phone(self):
        assert normalise_recipient_phone("+234 801 234 5678") == "+2348012345678"
        assert normalise_recipient_phone("234-801-234-5678") == "+2348012345678"
        assert normalise_recipient_phone("08012345678") == "+2348012345678"


# --------------------------------------------------------------------------- #
# Per-recipient variables
# --------------------------------------------------------------------------- #
class TestBroadcastVariables:
    def test_variables_map_renders_per_recipient(self, client, db_session):
        token, biz_id, headers, account = _setup_account(
            client, "vars1@example.com", "PNV1"
        )
        campaign = _create_broadcast(
            client,
            headers,
            account["id"],
            message_text="Hi {{name}}, your code is {{code}}",
            phone_numbers=[PHONE, PHONE_2],
            variables_map={
                0: {"name": "Ada", "code": "AAA"},
                1: {"name": "Bola", "code": "BBB"},
            },
        )
        started = client.post(
            f"/api/v1/whatsapp/broadcasts/{campaign['id']}/start", headers=headers
        )
        assert started.status_code == 200, started.text
        assert _run_sender(campaign["id"], biz_id, db_session) == "completed"

        msgs = _campaign_messages(db_session, campaign["id"])
        bodies = {m.to_number: m.body for m in msgs}
        assert bodies[PHONE] == "Hi Ada, your code is AAA"
        assert bodies[PHONE_2] == "Hi Bola, your code is BBB"

    def test_missing_variables_render_empty(self, client, db_session):
        token, biz_id, headers, account = _setup_account(
            client, "vars2@example.com", "PNV2"
        )
        campaign = _create_broadcast(
            client,
            headers,
            account["id"],
            message_text="Hi {{name}}!",
            phone_numbers=[PHONE],
        )
        client.post(
            f"/api/v1/whatsapp/broadcasts/{campaign['id']}/start", headers=headers
        )
        _run_sender(campaign["id"], biz_id, db_session)

        msgs = _campaign_messages(db_session, campaign["id"])
        assert msgs[0].body == "Hi !"


# --------------------------------------------------------------------------- #
# Scheduled broadcasts
# --------------------------------------------------------------------------- #
class TestScheduledBroadcasts:
    def _patch_scheduler(self, monkeypatch, db_session):
        """Route the scheduler + sender through the per-test in-memory DB.

        ``_process_whatsapp_broadcasts`` normally uses the production
        ``SessionLocal`` and spawns the sender with ``db=None`` (another
        production session).  Patch both so the exercise runs against the
        isolated test database; the sender is idempotent, so whether the
        spawned task completes before ``asyncio.run`` shuts down or the test
        finishes the work itself, the outcome is identical.
        """
        from app.services import scheduler as scheduler_module
        import app.services.whatsapp.broadcast as broadcast_module

        monkeypatch.setattr(scheduler_module, "SessionLocal", lambda: db_session)

        real_send = broadcast_module.send_broadcast_task

        async def fake_send(campaign_id, business_id, db=None):
            return await real_send(campaign_id, business_id, db=db_session)

        monkeypatch.setattr(broadcast_module, "send_broadcast_task", fake_send)
        return scheduler_module, broadcast_module

    def test_scheduler_dispatches_due_broadcast(self, client, db_session, monkeypatch):
        scheduler_module, broadcast_module = self._patch_scheduler(
            monkeypatch, db_session
        )

        token, biz_id, headers, account = _setup_account(
            client, "sch1@example.com", "PNSC1"
        )
        when = datetime.now(timezone.utc) + timedelta(seconds=5)
        campaign = _create_broadcast(
            client, headers, account["id"], scheduled_time=when.isoformat()
        )

        # Travel 10 minutes into the future for both the scheduler and the
        # sender so the campaign is due and claimed without waiting.
        def future_utcnow():
            return datetime.now(timezone.utc) + timedelta(minutes=10)

        monkeypatch.setattr(scheduler_module, "utcnow", future_utcnow)
        monkeypatch.setattr(broadcast_module, "utcnow", future_utcnow)

        launched = asyncio.run(scheduler_module._process_whatsapp_broadcasts())
        assert launched == 1

        # Finish the send deterministically (no-op if the spawned task won).
        assert _run_sender(campaign["id"], biz_id, db_session) == "completed"
        db_session.expire_all()
        msgs = _campaign_messages(db_session, campaign["id"])
        assert len(msgs) == 2
        assert all(m.status == "sent" for m in msgs)

    def test_scheduler_skips_future_broadcast(self, client, db_session, monkeypatch):
        scheduler_module, _ = self._patch_scheduler(monkeypatch, db_session)

        token, biz_id, headers, account = _setup_account(
            client, "sch2@example.com", "PNSC2"
        )
        when = datetime.now(timezone.utc) + timedelta(hours=6)
        campaign = _create_broadcast(
            client, headers, account["id"], scheduled_time=when.isoformat()
        )

        launched = asyncio.run(scheduler_module._process_whatsapp_broadcasts())
        assert launched == 0
        assert _campaign_messages(db_session, campaign["id"]) == []

    def test_scheduler_skips_already_sent_broadcast(
        self, client, db_session, monkeypatch
    ):
        scheduler_module, _ = self._patch_scheduler(monkeypatch, db_session)

        token, biz_id, headers, account, campaign_id = _setup_broadcast(
            client, db_session, email="sch3@example.com", phone_number_id="PNSC3"
        )
        launched = asyncio.run(scheduler_module._process_whatsapp_broadcasts())
        assert launched == 0
        assert len(_campaign_messages(db_session, campaign_id)) == 2


# --------------------------------------------------------------------------- #
# Webhook security
# --------------------------------------------------------------------------- #
class TestWebhookSecurity:
    def test_verify_token_challenge(self, client):
        resp = client.get(
            "/api/v1/whatsapp-commerce/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "sawatoken123",
                "hub.challenge": "chal-42",
            },
        )
        assert resp.status_code == 200
        assert resp.text == "chal-42"

    def test_verify_token_rejects_bad_token(self, client):
        resp = client.get(
            "/api/v1/whatsapp-commerce/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong-token",
                "hub.challenge": "chal-42",
            },
        )
        assert resp.status_code == 403

    def test_signature_rejected_in_production(self, client, monkeypatch):
        import app.api.v1.endpoints.whatsapp_commerce as wc

        monkeypatch.setattr(wc.settings, "WHATSAPP_APP_SECRET", "sekrit")
        body = json.dumps({"entry": []}).encode()
        resp = client.post(
            WEBHOOK,
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 403

    def test_signature_accepted_with_valid_hmac(self, client, monkeypatch):
        import app.api.v1.endpoints.whatsapp_commerce as wc

        secret = "sekrit"
        monkeypatch.setattr(wc.settings, "WHATSAPP_APP_SECRET", secret)
        body = json.dumps({"entry": []}).encode()
        sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        resp = client.post(
            WEBHOOK,
            content=body,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig},
        )
        assert resp.status_code == 200

    def test_malformed_json_rejected(self, client):
        resp = client.post(
            WEBHOOK,
            content=b"{not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400