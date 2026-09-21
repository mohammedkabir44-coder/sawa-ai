"""Analytics endpoints (dashboard counts + rich metrics)."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_membership
from app.core.database import get_db
from app.models.automation import Automation
from app.models.business import Business
from app.models.campaign import Campaign, CampaignRecipient
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.lead import Lead
from app.models.product import Product, Service
from app.models.sms import SMSMessage
from app.models.user import BusinessUser, User
from app.models.whatsapp import WhatsAppMessage
from app.schemas.analytics import (
    AnalyticsSummary,
    AiVsHuman,
    CampaignPerformance,
    DashboardQuickStats,
    DashboardResponse,
    LeadFunnelStage,
    MessageVolumePoint,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def analytics_summary(
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> AnalyticsSummary:
    """Return simple dashboard counts for the current business."""
    _, _, business = ctx

    total_customers = (
        db.query(Customer).filter(Customer.business_id == business.id).count()
    )
    total_leads = db.query(Lead).filter(Lead.business_id == business.id).count()
    total_products = (
        db.query(Product).filter(Product.business_id == business.id).count()
    )
    total_services = (
        db.query(Service).filter(Service.business_id == business.id).count()
    )
    new_leads = (
        db.query(Lead)
        .filter(Lead.business_id == business.id, Lead.stage == "new")
        .count()
    )
    won_leads = (
        db.query(Lead)
        .filter(Lead.business_id == business.id, Lead.stage == "won")
        .count()
    )

    return AnalyticsSummary(
        total_customers=total_customers,
        total_leads=total_leads,
        total_products=total_products,
        total_services=total_services,
        new_leads=new_leads,
        won_leads=won_leads,
    )


LEAD_STAGES = ["new", "contacted", "interested", "negotiating", "won", "lost"]
DASHBOARD_WINDOW_DAYS = 30


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _count(query) -> int:
    return query.count()


@router.get("/dashboard", response_model=DashboardResponse)
def analytics_dashboard(
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    """Rich analytics for the current business.

    Every query below is strictly filtered by ``business_id`` so tenants can
    only ever see their own numbers.
    """
    _, _, business = ctx
    biz = business.id
    now = _utcnow()
    window_start = now - timedelta(days=DASHBOARD_WINDOW_DAYS - 1)

    # ---- Message volume (WhatsApp + SMS), grouped by day, zero-filled ----
    wa_rows = (
        db.query(func.date(WhatsAppMessage.created_at).label("day"), func.count())
        .filter(
            WhatsAppMessage.business_id == biz,
            WhatsAppMessage.created_at >= window_start,
        )
        .group_by(func.date(WhatsAppMessage.created_at))
        .all()
    )
    sms_rows = (
        db.query(func.date(SMSMessage.created_at).label("day"), func.count())
        .filter(
            SMSMessage.business_id == biz,
            SMSMessage.created_at >= window_start,
        )
        .group_by(func.date(SMSMessage.created_at))
        .all()
    )

    wa_by_day: Dict[str, int] = {str(day): count for day, count in wa_rows}
    sms_by_day: Dict[str, int] = {str(day): count for day, count in sms_rows}

    message_volume: list[MessageVolumePoint] = []
    total_messages_30d = 0
    for offset in range(DASHBOARD_WINDOW_DAYS):
        day = (window_start + timedelta(days=offset)).date().isoformat()
        wa = wa_by_day.get(day, 0)
        sms = sms_by_day.get(day, 0)
        total_messages_30d += wa + sms
        message_volume.append(
            MessageVolumePoint(date=day, whatsapp=wa, sms=sms)
        )

    # ---- Lead funnel (fixed stage order) ----
    funnel_rows = dict(
        db.query(Lead.stage, func.count())
        .filter(Lead.business_id == biz)
        .group_by(Lead.stage)
        .all()
    )
    lead_funnel = [
        LeadFunnelStage(stage=stage, count=int(funnel_rows.get(stage, 0)))
        for stage in LEAD_STAGES
    ]
    won_leads = int(funnel_rows.get("won", 0))

    # ---- Campaign performance ----
    total_campaigns = (
        db.query(Campaign).filter(Campaign.business_id == biz).count()
    )
    recipient_status: Dict[str, int] = dict(
        db.query(CampaignRecipient.status, func.count())
        .join(Campaign, CampaignRecipient.campaign_id == Campaign.id)
        .filter(Campaign.business_id == biz)
        .group_by(CampaignRecipient.status)
        .all()
    )
    total_sent = int(recipient_status.get("sent", 0))
    total_delivered = int(recipient_status.get("delivered", 0))
    total_failed = int(recipient_status.get("failed", 0))
    attempted = total_sent + total_delivered + total_failed
    delivery_rate = round(total_delivered / attempted * 100, 1) if attempted else 0.0

    # ---- AI vs Human conversations ----
    ai_modes = ("AI_ACTIVE", "AI_PAUSED")
    ai_handled = (
        db.query(Conversation)
        .filter(
            Conversation.business_id == biz,
            Conversation.mode.in_(ai_modes),
        )
        .count()
    )
    human_handled = (
        db.query(Conversation)
        .filter(
            Conversation.business_id == biz,
            Conversation.mode == "HUMAN_ACTIVE",
        )
        .count()
    )

    active_automations = (
        db.query(Automation)
        .filter(Automation.business_id == biz, Automation.is_active.is_(True))
        .count()
    )

    return DashboardResponse(
        message_volume=message_volume,
        lead_funnel=lead_funnel,
        campaign_performance=CampaignPerformance(
            total_campaigns=total_campaigns,
            total_sent=total_sent,
            total_delivered=total_delivered,
            total_failed=total_failed,
        ),
        ai_vs_human=AiVsHuman(
            ai_handled=ai_handled, human_handled=human_handled
        ),
        stats=DashboardQuickStats(
            total_messages_30d=total_messages_30d,
            active_automations=active_automations,
            won_leads=won_leads,
            campaign_delivery_rate=delivery_rate,
        ),
    )