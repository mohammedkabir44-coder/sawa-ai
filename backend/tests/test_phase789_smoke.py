"""Smoke tests for Phase 7-9: voice-note transcription, SMS, campaigns.

These verify the new providers and endpoints work end-to-end with the mock
providers, and that strict tenant isolation is enforced on every new route.
"""
import pytest

from app.services.sms.mock import MockSMSProvider
from app.services.speech.mock import MockSpeechProvider
from app.services.whatsapp.mock import MockWhatsAppProvider


# --------------------------------------------------------------------------- #
# Phase 7 — voice-note transcription providers
# --------------------------------------------------------------------------- #
class TestVoiceNoteProviders:
    def test_mock_speech_returns_text_and_language(self):
        provider = MockSpeechProvider()
        result = provider.transcribe(b"fake-audio-bytes")
        assert result["text"]
        assert result["detected_language"] in ("ha", "en", "ha-en")
        assert result["provider"] == "mock"

    def test_mock_whatsapp_download_media(self):
        provider = MockWhatsAppProvider()
        data = provider.download_media("media-123")
        assert data == b"mock-audio-bytes-for-media-123"

    def test_mock_whatsapp_download_media_requires_id(self):
        provider = MockWhatsAppProvider()
        with pytest.raises(ValueError):
            provider.download_media("")


# --------------------------------------------------------------------------- #
# Phase 7 — audio webhook: download → transcribe → AI parse
# --------------------------------------------------------------------------- #
class TestWhatsAppAudioWebhook:
    def test_audio_webhook_transcribes_and_parses(self, client, monkeypatch):
        captured: dict = {}

        def fake_parse(message, catalog):
            captured["text"] = message
            return {
                "intent": "greeting",
                "reply_message": "Sannu! Ina taimakonka?",
                "detected_language": "ha",
            }

        monkeypatch.setattr(
            "app.api.v1.endpoints.whatsapp_commerce.parse_customer_intent",
            fake_parse,
        )

        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "2348012345678",
                                        "type": "audio",
                                        "audio": {"id": "audio-media-42"},
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

        # The AI parser must receive the transcript (not empty text).
        assert captured.get("text")
        assert "Ina son saya" in captured["text"]


# --------------------------------------------------------------------------- #
# Phase 8 — SMS provider + endpoints
# --------------------------------------------------------------------------- #
class TestSMS:
    def test_mock_sms_provider_returns_success(self):
        provider = MockSMSProvider()
        result = provider.send_sms("+2348012345678", "Hello")
        assert result["success"] is True
        assert result["message_id"].startswith("mock_")
        assert result["provider"] == "mock"

    def test_sms_send_and_history(self, client):
        # Register a user with a business (becomes owner of that tenant).
        reg = client.post(
            "/api/v1/auth/register",
            json={
                "email": "sms@example.com",
                "password": "password123",
                "full_name": "SMS Tester",
                "business_name": "SMS Co",
            },
        )
        assert reg.status_code == 201
        token = reg.json()["access_token"]

        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        biz_id = str(me.json()["memberships"][0]["business"]["id"])
        headers = {"Authorization": f"Bearer {token}", "X-Business-ID": biz_id}

        send = client.post(
            "/api/v1/sms/send",
            headers=headers,
            json={"phone": "+2348012345678", "message": "Hello SMS"},
        )
        assert send.status_code == 200
        body = send.json()
        assert body["success"] is True
        assert body["message_id"].startswith("mock_")

        history = client.get("/api/v1/sms/history", headers=headers)
        assert history.status_code == 200
        data = history.json()
        assert data["total"] >= 1
        assert data["items"][0]["to_phone"] == "+2348012345678"
        assert data["items"][0]["status"] == "sent"

    def test_sms_requires_auth(self, client):
        resp = client.post(
            "/api/v1/sms/send",
            json={"phone": "+2348012345678", "message": "No auth"},
        )
        assert resp.status_code in (401, 403)


# --------------------------------------------------------------------------- #
# Phase 9 — campaigns
# --------------------------------------------------------------------------- #
def _make_tenant(client, email: str, business_name: str):
    """Register a user + business, return (token, business_id)."""
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Campaign Tester",
            "business_name": business_name,
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    biz_id = str(me.json()["memberships"][0]["business"]["id"])
    return token, biz_id


def _create_customer(client, headers: dict, phone: str, tags=None):
    resp = client.post(
        "/api/v1/customers/",
        headers=headers,
        json={"name": "Customer", "phone": phone, "tags": tags or []},
    )
    assert resp.status_code == 201
    return resp.json()


class TestCampaigns:
    def test_campaign_crud_and_execute(self, client):
        token, biz_id = _make_tenant(client, "camp@example.com", "Camp Co")
        headers = {"Authorization": f"Bearer {token}", "X-Business-ID": biz_id}

        _create_customer(client, headers, "+2348011111111", tags=["VIP"])
        _create_customer(client, headers, "+2348022222222", tags=["regular"])

        # Create a campaign targeting VIPs via SMS.
        create = client.post(
            "/api/v1/campaigns/",
            headers=headers,
            json={
                "name": "VIP Offer",
                "channel": "sms",
                "audience": {"tags": ["VIP"]},
                "message": "Exclusive 20% off for VIPs!",
            },
        )
        assert create.status_code == 201
        campaign = create.json()
        assert campaign["status"] == "draft"
        assert campaign["audience"] == {"tags": ["VIP"]}

        # List shows the new campaign.
        listing = client.get("/api/v1/campaigns/", headers=headers)
        assert listing.status_code == 200
        assert listing.json()["total"] >= 1
        assert listing.json()["items"][0]["name"] == "VIP Offer"

        # Execute sends to the single VIP customer only.
        execute = client.post(
            f"/api/v1/campaigns/{campaign['id']}/execute", headers=headers
        )
        assert execute.status_code == 200
        result = execute.json()
        assert result["total"] == 1
        assert result["sent"] == 1
        assert result["failed"] == 0
        assert result["status"] == "completed"

        # Re-executing a completed campaign is refused.
        again = client.post(
            f"/api/v1/campaigns/{campaign['id']}/execute", headers=headers
        )
        assert again.status_code == 400

    def test_campaign_tenant_isolation(self, client):
        token_a, biz_a = _make_tenant(client, "tenanta@example.com", "Tenant A")
        token_b, biz_b = _make_tenant(client, "tenantb@example.com", "Tenant B")
        headers_a = {"Authorization": f"Bearer {token_a}", "X-Business-ID": biz_a}
        headers_b = {"Authorization": f"Bearer {token_b}", "X-Business-ID": biz_b}

        # A creates a campaign.
        create = client.post(
            "/api/v1/campaigns/",
            headers=headers_a,
            json={
                "name": "A Only",
                "channel": "whatsapp",
                "audience": {"all": True},
                "message": "For A only",
            },
        )
        assert create.status_code == 201
        campaign_a_id = create.json()["id"]

        # B cannot see A's campaign.
        list_b = client.get("/api/v1/campaigns/", headers=headers_b)
        assert list_b.status_code == 200
        assert all(c["id"] != campaign_a_id for c in list_b.json()["items"])

        # B cannot fetch or execute A's campaign (404 — never leaks existence).
        get_b = client.get(f"/api/v1/campaigns/{campaign_a_id}", headers=headers_b)
        assert get_b.status_code == 404
        exec_b = client.post(
            f"/api/v1/campaigns/{campaign_a_id}/execute", headers=headers_b
        )
        assert exec_b.status_code == 404

    def test_sms_history_tenant_isolation(self, client):
        token_a, biz_a = _make_tenant(client, "smsa@example.com", "SMS A")
        token_b, biz_b = _make_tenant(client, "smsb@example.com", "SMS B")
        headers_a = {"Authorization": f"Bearer {token_a}", "X-Business-ID": biz_a}
        headers_b = {"Authorization": f"Bearer {token_b}", "X-Business-ID": biz_b}

        client.post(
            "/api/v1/sms/send",
            headers=headers_a,
            json={"phone": "+2348099999999", "message": "A's message"},
        )

        hist_b = client.get("/api/v1/sms/history", headers=headers_b)
        assert hist_b.status_code == 200
        assert hist_b.json()["total"] == 0