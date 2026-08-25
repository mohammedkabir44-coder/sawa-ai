"""Simple audit-logging helper for sensitive actions."""
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


def log_audit(
    db: Session,
    *,
    user_id: Optional[int] = None,
    business_id: Optional[int] = None,
    action: str,
    details: str = "",
    resource_type: str = "",
    resource_id: str = "",
    commit: bool = True,
) -> AuditLog:
    """Record an audit entry for a sensitive action.

    Best-effort by design: callers should already have committed their
    primary change; a failed audit write is logged but never raised so it
    cannot mask the outcome of the original operation.

    Args:
        db: Active database session.
        user_id: The acting user (if known).
        business_id: Tenant context (if known).
        action: Short machine-readable action, e.g. ``automation.deleted``.
        details: Human-readable description.
        resource_type / resource_id: What was acted upon.
        commit: Whether to commit immediately (set False to batch).
    """
    try:
        entry = AuditLog(
            user_id=user_id,
            business_id=business_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id or ""),
            details=details,
        )
        db.add(entry)
        if commit:
            db.commit()
        return entry
    except Exception as exc:  # noqa: BLE001
        # Audit writes must never mask the outcome of the primary operation.
        logger.warning("Failed to write audit log for %s: %s", action, exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return None