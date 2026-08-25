"""Smoke tests for Phase 10: Automation Engine & background jobs.

Verifies:
* Automation CRUD + active toggle + step replacement (tenant-scoped).
* Tenant isolation on every automation route.
* ``execute_automation`` runs steps in order (add_tag / send_sms / failure path).
* The WhatsApp webhook fires the ``whatsapp_message_received`` trigger.
"""
import asyncio

from app.models.automation import Automation, AutomationRun, AutomationStep
from app.models.customer import Customer
from app.models.whatsapp import WhatsAppAccount
from app.services.workflow_engine import execute_automation


def _make_tenant(client, email: str, business_name: str):
    """Register a user + business; return (token, business_id)."""
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Auto Tester",
            "business_name": business_name,
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    biz_id = str(me.json()["memberships"][0]["business"]["id"])
    return token, biz_id


STEPS = [
    {
        "step_type": "action",
        "action_type": "send_whatsapp",
        "config": {"message": "Welcome!"},
        "order_index": 0,
    },
    {
        "step_type": "delay",
        "action_type": "wait_delay",
        "config": {"seconds": 0},
        "order_index": 1,
    },
    {
        "step_type": "action",
        "action_type": "add_tag",
        "config": {"tag": "auto-welcomed"},
        "order_index": 2,
    },
]


class TestAutomationAPI:
    def test_create_list_detail_toggle_and_replace_steps(self, client):
        token, biz_id = _make_tenant(client, "auto@example.com", "Auto Co")
        headers = {"Authorization": f"Bearer {token}", "X-Business-ID": biz_id}

        create = client.post(
            "/api/v1/automations/",
            headers=headers,
            json={
                "name": "Welcome Flow",
                "trigger_type": "whatsapp_message_received",
                "is_active": True,
                "steps": STEPS,
            },
        )
        assert create.status_code == 201
        automation = create.json()
        assert automation["business_id"] == int(biz_id)
        assert automation["is_active"] is True

        listing = client.get("/api/v1/automations/", headers=headers)
        assert listing.status_code == 200
        assert listing.json()["total"] == 1
        assert listing.json()["items"][0]["name"] == "Welcome Flow"

        detail = client.get(
            f"/api/v1/automations/{automation['id']}", headers=headers
        )
        assert detail.status_code == 200
        steps = detail.json()["steps"]
        assert [s["position"] for s in steps] == [0, 1, 2]
        assert [s["step_type"] for s in steps] == ["action", "delay", "action"]

        # Toggle inactive via PATCH.
        patch = client.patch(
            f"/api/v1/automations/{automation['id']}",
            headers=headers,
            json={"is_active": False},
        )
        assert patch.status_code == 200
        assert patch.json()["is_active"] is False

        # Toggle back on and replace steps with a single send_sms action.
        patch2 = client.patch(
            f"/api/v1/automations/{automation['id']}",
            headers=headers,
            json={
                "is_active": True,
                "steps": [
                    {
                        "step_type": "action",
                        "action_type": "send_sms",
                        "config": {},
                        "order_index": 0,
                    }
                ],
            },
        )
        assert patch2.status_code == 200
        assert patch2.json()["is_active"] is True

        detail2 = client.get(
            f"/api/v1/automations/{automation['id']}", headers=headers
        )
        new_steps = detail2.json()["steps"]
        assert len(new_steps) == 1
        assert new_steps[0]["action_type"] == "send_sms"

    def test_invalid_trigger_rejected(self, client):
        token, biz_id = _make_tenant(client, "badtrig@example.com", "BadTrig Co")
        headers = {"Authorization": f"Bearer {token}", "X-Business-ID": biz_id}
        resp = client.post(
            "/api/v1/automations/",
            headers=headers,
            json={"name": "X", "trigger_type": "not_a_trigger", "steps": []},
        )
        assert resp.status_code == 422

    def test_requires_auth(self, client):
        resp = client.get("/api/v1/automations/")
        assert resp.status_code in (401, 403)

    def test_tenant_isolation(self, client):
        token_a, biz_a = _make_tenant(client, "auta@example.com", "Auto A")
        token_b, biz_b = _make_tenant(client, "autb@example.com", "Auto B")
        headers_a = {"Authorization": f"Bearer {token_a}", "X-Business-ID": biz_a}
        headers_b = {"Authorization": f"Bearer {token_b}", "X-Business-ID": biz_b}

        create = client.post(
            "/api/v1/automations/",
            headers=headers_a,
            json={
                "name": "A Only Flow",
                "trigger_type": "new_lead_created",
                "steps": [],
            },
        )
        assert create.status_code == 201
        auto_id = create.json()["id"]

        # B's list never contains A's automation.
        list_b = client.get("/api/v1/automations/", headers=headers_b)
        assert list_b.status_code == 200
        assert all(a["id"] != auto_id for a in list_b.json()["items"])

        # B cannot fetch, patch or delete A's automation (404 — no leak).
        assert (
            client.get(f"/api/v1/automations/{auto_id}", headers=headers_b).status_code
            == 404
        )
        assert (
            client.patch(
                f"/api/v1/automations/{auto_id}",
                headers=headers_b,
                json={"is_active": False},
            ).status_code
            == 404
        )
        assert (
            client.delete(
                f"/api/v1/automations/{auto_id}", headers=headers_b
            ).status_code
            == 404
        )

        # Owner of A can delete their own automation.
        assert (
            client.delete(f"/api/v1/automations/{auto_id}", headers=headers_a).status_code
            == 204
        )


class TestAutomationExecution:
    def test_execute_add_tag_updates_customer(self, client, db_session):
        customer = Customer(business_id=1, name="Tag Me", phone="+2348012340000")
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)

        automation = Automation(
            business_id=1,
            name="tagger",
            trigger_type="whatsapp_message_received",
            is_active=True,
        )
        db_session.add(automation)
        db_session.flush()
        db_session.add(
            AutomationStep(
                automation_id=automation.id,
                step_type="action",
                action_type="add_tag",
                config='{"tag": "vip-auto"}',
                position=0,
            )
        )
        db_session.commit()

        run_id = asyncio.run(
            execute_automation(
                automation.id,
                {"phone": customer.phone, "business_id": 1},
                db=db_session,
            )
        )
        assert run_id is not None

        run = db_session.get(AutomationRun, run_id)
        assert run is not None
        assert run.status == "completed"

        db_session.refresh(customer)
        assert "vip-auto" in customer.tags

    def test_execute_send_sms_completes_with_mock(self, client, db_session):
        automation = Automation(
            business_id=1,
            name="sms greeter",
            trigger_type="whatsapp_message_received",
            is_active=True,
        )
        db_session.add(automation)
        db_session.flush()
        db_session.add(
            AutomationStep(
                automation_id=automation.id,
                step_type="action",
                action_type="send_sms",
                config='{"message": "Hello from SAWA"}',
                position=0,
            )
        )
        db_session.commit()

        run_id = asyncio.run(
            execute_automation(
                automation.id,
                {"phone": "+2348099998888", "business_id": 1},
                db=db_session,
            )
        )
        assert run_id is not None
        run = db_session.get(AutomationRun, run_id)
        assert run.status == "completed"

    def test_missing_phone_marks_run_failed(self, client, db_session):
        automation = Automation(
            business_id=1,
            name="broken sender",
            trigger_type="whatsapp_message_received",
            is_active=True,
        )
        db_session.add(automation)
        db_session.flush()
        db_session.add(
            AutomationStep(
                automation_id=automation.id,
                step_type="action",
                action_type="send_whatsapp",
                config='{"message": "no phone"}',
                position=0,
            )
        )
        db_session.commit()

        run_id = asyncio.run(
            execute_automation(automation.id, {"business_id": 1}, db=db_session)
        )
        assert run_id is not None
        run = db_session.get(AutomationRun, run_id)
        assert run.status == "failed"
        assert "phone" in run.error.lower()


class TestWebhookTriggerHook:
    def test_webhook_fires_message_received_trigger(
        self, client, db_session, monkeypatch
    ):
        """Inbound WhatsApp messages must fire matching active automations."""
        captured: dict = {}

        async def fake_trigger(business_id, trigger_type, context_data, db=None):
            captured["business_id"] = business_id
            captured["trigger_type"] = trigger_type
            captured["context"] = dict(context_data)
            return 0

        monkeypatch.setattr(
            "app.api.v1.endpoints.whatsapp_commerce.trigger_automations",
            fake_trigger,
        )

        # A WhatsApp account so the webhook can resolve the tenant.
        account = WhatsAppAccount(
            business_id=1,
            phone_number="15551234567",
            api_key="dummy-key",
            is_connected=True,
        )
        db_session.add(account)
        db_session.commit()

        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+2348012345678",
                                        "to": "15551234567",
                                        "type": "text",
                                        "text": {"body": "Hello!"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        resp = client.post("/api/v1/whatsapp-commerce/webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

        assert captured.get("trigger_type") == "whatsapp_message_received"
        assert captured.get("business_id") == 1
        assert captured["context"]["phone"] == "+2348012345678"