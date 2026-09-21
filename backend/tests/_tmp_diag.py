"""Diagnostic: how do require_permission vs require_membership resolve business?"""
import asyncio

from app.models.user import BusinessUser
from app.models.whatsapp import WhatsAppCampaign
from app.services.whatsapp.broadcast import send_broadcast_task

from tests.test_whatsapp_broadcast import (
    _create_account,
    _create_broadcast,
    _headers,
    _make_tenant,
)


def test_diagnose_business_resolution(client, db_session, caplog):
    import logging

    from app.models.whatsapp import WhatsAppTemplate

    token, biz_id = _make_tenant(client, "diag@example.com", "Diag Co")
    headers = _headers(token, biz_id)
    account = _create_account(client, headers, "PNDIAG")
    campaign = _create_broadcast(client, headers, account["id"])

    tpl = client.post(
        "/api/v1/whatsapp/templates",
        json={"template_name": "t1", "template_text": "x"},
        headers=headers,
    )
    assert tpl.status_code in (200, 201), tpl.text

    print("\n!!! header biz_id =", biz_id)
    print("!!! memberships:", [(m.business_id, m.is_active) for m in db_session.query(BusinessUser).all()])
    row = db_session.get(WhatsAppCampaign, campaign["id"])
    print("!!! campaign row business_id =", row.business_id if row else None)
    trow = db_session.query(WhatsAppTemplate).filter(WhatsAppTemplate.template_name == "t1").first()
    print("!!! template row business_id =", trow.business_id if trow else None)
    arow = db_session.get(type(trow), 0)  # placeholder no-op
    print("!!! account row business_id =", db_session.query(type(trow)).count())

    listed = client.get("/api/v1/whatsapp/templates", headers=headers)
    print("!!! template list status:", listed.status_code, "items:", len(listed.json().get("items", [])))
    blisted = client.get("/api/v1/whatsapp/broadcasts", headers=headers)
    print("!!! broadcast list total:", blisted.json().get("total"))

    logging.basicConfig(level=logging.WARNING)
    started = client.post(
        f"/api/v1/whatsapp/broadcasts/{campaign['id']}/start", headers=headers
    )
    print("!!! start status:", started.status_code, started.json().get("status"))

    with caplog.at_level(logging.WARNING):
        result = asyncio.run(
            send_broadcast_task(campaign["id"], biz_id, db=db_session)
        )
    print("!!! sender result:", result)
    print("!!! caplog:", [r.getMessage() for r in caplog.records])
    assert True
