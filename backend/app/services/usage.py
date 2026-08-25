"""Usage tracking and limits.

Tracks monthly usage per business. Limits come from the business's plan
(parsed from the plan's JSON `limits` field). When a limit is reached the
caller is informed so it can show a clear message.
"""
import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.billing import Plan, Subscription
from app.models.usage import UsageRecord

DEFAULT_LIMITS = {
    "monthly_ai_messages": 100,
    "monthly_sms": 50,
    "monthly_whatsapp_messages": 200,
    "active_automations": 5,
    "customers": 500,
    "staff_members": 3,
}


def _period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def get_limits(db: Session, business_id: int) -> dict:
    sub = (
        db.query(Subscription)
        .filter(Subscription.business_id == business_id)
        .order_by(Subscription.id.desc())
        .first()
    )
    if sub is None:
        return dict(DEFAULT_LIMITS)
    plan = db.get(Plan, sub.plan_id)
    if plan is None:
        return dict(DEFAULT_LIMITS)
    try:
        limits = json.loads(plan.limits or "{}")
    except json.JSONDecodeError:
        limits = {}
    merged = dict(DEFAULT_LIMITS)
    merged.update(limits)
    return merged


def get_usage(db: Session, business_id: int, metric: str) -> int:
    record = (
        db.query(UsageRecord)
        .filter(
            UsageRecord.business_id == business_id,
            UsageRecord.metric == metric,
            UsageRecord.period == _period(),
        )
        .first()
    )
    return record.value if record else 0


def increment_usage(db: Session, business_id: int, metric: str, amount: int = 1) -> int:
    record = (
        db.query(UsageRecord)
        .filter(
            UsageRecord.business_id == business_id,
            UsageRecord.metric == metric,
            UsageRecord.period == _period(),
        )
        .first()
    )
    if record is None:
        record = UsageRecord(
            business_id=business_id,
            metric=metric,
            value=amount,
            period=_period(),
        )
        db.add(record)
    else:
        record.value += amount
    db.commit()
    return record.value


def check_limit(db: Session, business_id: int, metric: str) -> tuple[bool, int, int]:
    """Return (allowed, current, limit)."""
    limits = get_limits(db, business_id)
    limit = limits.get(metric, 0)
    current = get_usage(db, business_id, metric)
    return (current < limit, current, limit)


def usage_summary(db: Session, business_id: int) -> dict:
    limits = get_limits(db, business_id)
    summary = {}
    for metric, limit in limits.items():
        current = get_usage(db, business_id, metric)
        summary[metric] = {
            "value": current,
            "limit": limit,
            "remaining": max(0, limit - current),
            "period": _period(),
        }
    return summary