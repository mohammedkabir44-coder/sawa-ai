"""Lightweight background worker for scheduled automation + campaign execution.

Uses a simple asyncio loop (no APScheduler dependency) that polls the database
every ``JOB_POLL_INTERVAL_SECONDS`` seconds.  Responsibilities:

* Fire ``scheduled_time`` automations whose ``trigger_config.run_at`` is due.
* Execute campaigns whose ``Campaign.schedule_at`` is due (and not already run).

The worker is intentionally disabled while running under ``pytest`` so test
runs never touch the on-disk dev database.
"""
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.automation import Automation
from app.models.campaign import Campaign
from app.services.workflow_engine import execute_automation

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_testing() -> bool:
    """Return True when running under pytest (worker must stay quiet)."""
    return "pytest" in sys.modules


def _parse_run_at(raw: Any) -> Optional[datetime]:
    """Best-effort ISO-8601 datetime parsing; naive values become UTC."""
    try:
        run_at = datetime.fromisoformat(str(raw))
    except (ValueError, TypeError):
        return None
    if run_at.tzinfo is None:
        run_at = run_at.replace(tzinfo=timezone.utc)
    return run_at


async def _process_scheduled_automations() -> int:
    """Fire due ``scheduled_time`` automations. Returns how many were fired."""
    db = SessionLocal()
    fired = 0
    try:
        now = utcnow()
        automations = (
            db.query(Automation)
            .filter(
                Automation.is_active.is_(True),
                Automation.trigger_type == "scheduled_time",
            )
            .all()
        )
        for automation in automations:
            try:
                config = json.loads(automation.trigger_config or "{}")
                if not isinstance(config, dict) or not config.get("run_at"):
                    continue
                run_at = _parse_run_at(config.get("run_at"))
                if run_at is None:
                    continue
                if run_at <= now:
                    fired += 1
                    try:
                        asyncio.create_task(
                            execute_automation(
                                automation.id,
                                {"business_id": automation.business_id},
                            )
                        )
                    except RuntimeError:
                        await execute_automation(
                            automation.id,
                            {"business_id": automation.business_id},
                        )
            except Exception:  # noqa: BLE001
                logger.exception(
                    "Scheduler failed to process automation %s", automation.id
                )
    finally:
        db.close()
    return fired


async def _process_scheduled_campaigns() -> int:
    """Execute campaigns whose ``schedule_at`` is due. Returns executed count."""
    db = SessionLocal()
    executed = 0
    try:
        from app.api.v1.endpoints.campaigns import run_campaign_execution

        now = utcnow()
        campaigns = (
            db.query(Campaign)
            .filter(
                Campaign.schedule_at.isnot(None),
                Campaign.schedule_at <= now,
                Campaign.status.in_(["draft", "scheduled"]),
            )
            .all()
        )
        for campaign in campaigns:
            try:
                await run_campaign_execution(db, campaign, user_id=None)
                executed += 1
            except Exception:  # noqa: BLE001
                logger.exception(
                    "Scheduler failed to run campaign %s", campaign.id
                )
    finally:
        db.close()
    return executed


async def run_worker(stop_event: Optional[asyncio.Event] = None) -> None:
    """Main background loop. Returns immediately if disabled."""
    interval = int(settings.JOB_POLL_INTERVAL_SECONDS or 0)
    if interval <= 0:
        logger.info(
            "Background worker disabled (JOB_POLL_INTERVAL_SECONDS=%s)", interval
        )
        return
    if _is_testing():
        logger.info("Background worker disabled while running under pytest")
        return

    logger.info(
        "Background worker started (poll interval %ss)", interval
    )
    while True:
        try:
            fired = await _process_scheduled_automations()
            if fired:
                logger.info("Scheduler fired %s scheduled automation(s)", fired)
            ran = await _process_scheduled_campaigns()
            if ran:
                logger.info("Scheduler ran %s scheduled campaign(s)", ran)
        except Exception:  # noqa: BLE001
            logger.exception("Background worker cycle failed")

        # Sleep until the next poll or until asked to stop.
        try:
            if stop_event is not None:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
            else:
                await asyncio.sleep(interval)
        except asyncio.TimeoutError:
            continue
        except asyncio.CancelledError:
            logger.info("Background worker stopped")
            break