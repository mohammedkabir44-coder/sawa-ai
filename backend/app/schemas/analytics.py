"""Analytics schemas."""
from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_customers: int
    new_leads: int
    open_conversations: int
    whatsapp_received: int
    whatsapp_sent: int
    sms_sent: int
    campaigns_created: int
    conversion_rate: float
    ai_conversations: int
    human_conversations: int
    follow_ups_pending: int
    failed_messages: int
    ai_failures: int
    usage: dict[str, int] = {}


class UsageOut(BaseModel):
    metric: str
    value: int
    limit: int
    remaining: int
    period: str


class AnalyticsSummary(BaseModel):
    """Simple dashboard counts for Phase 3."""

    total_customers: int
    total_leads: int
    total_products: int
    total_services: int
    new_leads: int
    won_leads: int

# ---------------------------------------------------------------------------
# Phase 11 — rich dashboard metrics
# ---------------------------------------------------------------------------
class MessageVolumePoint(BaseModel):
    """One day of message counts (zero-filled across the 30-day window)."""

    date: str  # ISO date, e.g. 2026-08-24
    whatsapp: int = 0
    sms: int = 0


class LeadFunnelStage(BaseModel):
    stage: str
    count: int


class CampaignPerformance(BaseModel):
    total_campaigns: int
    total_sent: int
    total_delivered: int
    total_failed: int


class AiVsHuman(BaseModel):
    ai_handled: int
    human_handled: int


class DashboardQuickStats(BaseModel):
    total_messages_30d: int
    active_automations: int
    won_leads: int
    campaign_delivery_rate: float  # percentage 0-100


class DashboardResponse(BaseModel):
    message_volume: list[MessageVolumePoint]
    lead_funnel: list[LeadFunnelStage]
    campaign_performance: CampaignPerformance
    ai_vs_human: AiVsHuman
    stats: DashboardQuickStats
