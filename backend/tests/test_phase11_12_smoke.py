"""Smoke tests for Phase 11 (Analytics) & Phase 12 (Security hardening)."""
from app.models.audit import AuditLog


def _make_tenant(client, email: str, business_name: str):
    """Register a user + business; return (token, business_id)."""
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Analytics Tester",
            "business_name": business_name,
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    payload = me.json()
    biz_id = str(payload["memberships"][0]["business"]["id"])
    return token, biz_id, payload["user"]["id"]


class TestAnalyticsDashboard:
    def test_dashboard_structure_and_data(self, client):
        token, biz_id, _user_id = _make_tenant(
            client, "ana@example.com", "Ana Co"
        )
        headers = {"Authorization": f"Bearer {token}", "X-Business-ID": biz_id}

        # Seed: an active automation, a won lead, and an SMS message today.
        auto = client.post(
            "/api/v1/automations/",
            headers=headers,
            json={
                "name": "Dash Auto",
                "trigger_type": "whatsapp_message_received",
                "steps": [],
            },
        )
        assert auto.status_code == 201

        cust = client.post(
            "/api/v1/customers/",
            headers=headers,
            json={"name": "Cust", "phone": "+2348011112222"},
        )
        assert cust.status_code == 201

        lead = client.post(
            "/api/v1/leads/",
            headers=headers,
            json={"customer_id": cust.json()["id"], "stage": "won"},
        )
        assert lead.status_code == 201

        sms = client.post(
            "/api/v1/sms/send",
            headers=headers,
            json={"phone": "+2348011112222", "message": "volume test"},
        )
        assert sms.status_code == 200

        resp = client.get("/api/v1/analytics/dashboard", headers=headers)
        assert resp.status_code == 200
        body = resp.json()

        # Structure.
        assert set(body) >= {
            "message_volume",
            "lead_funnel",
            "campaign_performance",
            "ai_vs_human",
            "stats",
        }
        assert len(body["message_volume"]) == 30
        stages = [s["stage"] for s in body["lead_funnel"]]
        assert stages == [
            "new",
            "contacted",
            "interested",
            "negotiating",
            "won",
            "lost",
        ]

        # Data seeded above must show up.
        today = body["message_volume"][-1]
        assert today["sms"] >= 1
        won = [s for s in body["lead_funnel"] if s["stage"] == "won"][0]
        assert won["count"] == 1
        assert body["stats"]["active_automations"] == 1
        assert body["stats"]["won_leads"] == 1
        assert body["campaign_performance"]["total_campaigns"] == 0
        assert body["stats"]["campaign_delivery_rate"] == 0.0

    def test_dashboard_tenant_isolation(self, client):
        token_a, biz_a, _ = _make_tenant(client, "anaa@example.com", "Ana A")
        token_b, biz_b, _ = _make_tenant(client, "anab@example.com", "Ana B")
        headers_a = {"Authorization": f"Bearer {token_a}", "X-Business-ID": biz_a}
        headers_b = {"Authorization": f"Bearer {token_b}", "X-Business-ID": biz_b}

        # A creates an active automation and sends an SMS.
        client.post(
            "/api/v1/automations/",
            headers=headers_a,
            json={"name": "A flow", "trigger_type": "new_lead_created"},
        )
        client.post(
            "/api/v1/sms/send",
            headers=headers_a,
            json={"phone": "+2348000000001", "message": "A only"},
        )

        dash_a = client.get("/api/v1/analytics/dashboard", headers=headers_a)
        dash_b = client.get("/api/v1/analytics/dashboard", headers=headers_b)
        assert dash_a.status_code == 200 and dash_b.status_code == 200

        a = dash_a.json()
        b = dash_b.json()

        assert a["stats"]["active_automations"] == 1
        assert b["stats"]["active_automations"] == 0
        assert a["stats"]["total_messages_30d"] >= 1
        assert b["stats"]["total_messages_30d"] == 0
        assert sum(s["count"] for s in b["lead_funnel"]) == 0


class TestSecurityHardening:
    def test_global_error_handler_returns_clean_500(
        self, monkeypatch
    ):
        """Unhandled exceptions must produce JSON 500 without leaking traces.

        ServerErrorMiddleware always re-raises after the custom handler
        responds, so we use a TestClient that does not convert that into a
        test failure — this mirrors what a real server/client sees.
        """
        from fastapi.testclient import TestClient

        from app.main import app

        def boom(message, catalog):
            raise RuntimeError("secret internal detail")

        monkeypatch.setattr(
            "app.api.v1.endpoints.whatsapp_commerce.parse_customer_intent",
            boom,
        )
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.post(
                "/api/v1/whatsapp-commerce/parse", json={"message": "hi"}
            )
        assert resp.status_code == 500
        assert resp.json() == {"detail": "Internal server error"}
        assert "boom" not in resp.text
        assert "RuntimeError" not in resp.text

    def test_audit_log_on_automation_delete(self, client, db_session):
        token, biz_id, user_id = _make_tenant(
            client, "aud@example.com", "Audit Co"
        )
        headers = {"Authorization": f"Bearer {token}", "X-Business-ID": biz_id}

        created = client.post(
            "/api/v1/automations/",
            headers=headers,
            json={
                "name": "Doomed Flow",
                "trigger_type": "new_lead_created",
                "steps": [],
            },
        )
        assert created.status_code == 201
        auto_id = created.json()["id"]

        deleted = client.delete(
            f"/api/v1/automations/{auto_id}", headers=headers
        )
        assert deleted.status_code == 204

        logs = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.business_id == int(biz_id),
                AuditLog.action == "automation.deleted",
            )
            .all()
        )
        assert len(logs) == 1
        entry = logs[0]
        assert entry.user_id == user_id
        assert entry.resource_type == "automation"
        assert entry.resource_id == str(auto_id)
        assert "Doomed Flow" in entry.details