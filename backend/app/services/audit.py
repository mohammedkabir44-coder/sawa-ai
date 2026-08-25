"""Audit logging helper."""
from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def record_audit(
    db: Session,
    action: str,
    business_id: int | None = None,
    user_id: int | None = None,
    resource_type: str = "",
    resource_id: str = "",
    details: str = "",
    ip_address: str = "",
) -> None:
    entry = AuditLog(
        business_id=business_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()