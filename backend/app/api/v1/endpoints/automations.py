"""Automation endpoints (tenant-scoped CRUD)."""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    require_business_owner,
    require_membership,
    require_permission,
)
from app.core.database import get_db
from app.models.automation import Automation, AutomationStep
from app.models.business import Business
from app.models.user import BusinessUser, User
from app.schemas.automation import (
    AutomationCreate,
    AutomationDetail,
    AutomationList,
    AutomationOut,
    AutomationStepCreate,
    AutomationUpdate,
)
from app.services.audit_service import log_audit

router = APIRouter(prefix="/automations", tags=["automations"])

logger = logging.getLogger(__name__)


def _get_automation_or_404(
    db: Session, business_id: int, automation_id: int
) -> Automation:
    """Fetch an automation that belongs to the given business or raise 404."""
    automation = (
        db.query(Automation)
        .filter(
            Automation.id == automation_id,
            Automation.business_id == business_id,
        )
        .first()
    )
    if automation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found",
        )
    return automation


def _add_steps(
    db: Session, automation_id: int, steps: list[AutomationStepCreate]
) -> None:
    """Persist a list of steps onto an automation, ordered by order_index."""
    for index, step in enumerate(steps):
        db.add(
            AutomationStep(
                automation_id=automation_id,
                step_type=step.step_type,
                action_type=step.action_type or "",
                config=json.dumps(step.config or {}),
                position=step.order_index if step.order_index else index,
                is_enabled=step.is_enabled,
            )
        )


@router.post(
    "/", response_model=AutomationOut, status_code=status.HTTP_201_CREATED
)
def create_automation(
    payload: AutomationCreate,
    ctx: tuple[User, BusinessUser, Business] = Depends(
        require_permission("manage_automations")
    ),
    db: Session = Depends(get_db),
) -> AutomationOut:
    """Create an automation with its ordered steps for the current business.

    Tenant isolation: business_id always comes from the active membership
    resolved via the X-Business-ID header — never from the payload.
    """
    user, _, business = ctx
    automation = Automation(
        business_id=business.id,
        name=payload.name,
        description=payload.description or "",
        trigger_type=payload.trigger_type,
        trigger_config=json.dumps(payload.trigger_config or {}),
        is_active=payload.is_active,
        created_by=user.id,
    )
    db.add(automation)
    db.flush()  # assign automation.id so steps can reference it
    _add_steps(db, automation.id, payload.steps)
    db.commit()
    db.refresh(automation)
    return AutomationOut.model_validate(automation)


@router.get("/", response_model=AutomationList)
def list_automations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> AutomationList:
    """List automations for the current business, newest first."""
    _, _, business = ctx
    query = db.query(Automation).filter(Automation.business_id == business.id)

    total = query.count()
    automations = (
        query.order_by(Automation.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [AutomationOut.model_validate(a) for a in automations]
    return AutomationList(items=items, total=total)


@router.get("/{automation_id}", response_model=AutomationDetail)
def get_automation(
    automation_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> AutomationDetail:
    """Return a single automation with its steps (tenant-scoped)."""
    _, _, business = ctx
    automation = _get_automation_or_404(db, business.id, automation_id)

    steps = (
        db.query(AutomationStep)
        .filter(AutomationStep.automation_id == automation.id)
        .order_by(AutomationStep.position.asc())
        .all()
    )
    base = AutomationOut.model_validate(automation)
    return AutomationDetail(**base.model_dump(), steps=steps)


@router.patch("/{automation_id}", response_model=AutomationOut)
def update_automation(
    automation_id: int,
    payload: AutomationUpdate,
    ctx: tuple[User, BusinessUser, Business] = Depends(
        require_permission("manage_automations")
    ),
    db: Session = Depends(get_db),
) -> AutomationOut:
    """Update an automation: toggle active, rename, or replace its steps."""
    _, _, business = ctx
    automation = _get_automation_or_404(db, business.id, automation_id)

    data = payload.model_dump(exclude_unset=True)

    if data.get("name") is not None:
        automation.name = data["name"]
    if data.get("description") is not None:
        automation.description = data["description"]
    if data.get("trigger_type") is not None:
        automation.trigger_type = data["trigger_type"]
    if data.get("trigger_config") is not None:
        automation.trigger_config = json.dumps(data["trigger_config"])
    if data.get("is_active") is not None:
        automation.is_active = data["is_active"]

    if data.get("steps") is not None:
        # Replace steps wholesale — simplest reliable V1 behavior.
        db.query(AutomationStep).filter(
            AutomationStep.automation_id == automation.id
        ).delete()
        _add_steps(db, automation.id, payload.steps)

    db.commit()
    db.refresh(automation)
    return AutomationOut.model_validate(automation)


@router.delete("/{automation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_automation(
    automation_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_owner),
    db: Session = Depends(get_db),
) -> None:
    """Delete an automation. Owner-only (or platform admin)."""
    user, _, business = ctx
    automation = _get_automation_or_404(db, business.id, automation_id)

    automation_name = automation.name
    db.delete(automation)
    db.commit()

    log_audit(
        db,
        user_id=user.id,
        business_id=business.id,
        action="automation.deleted",
        resource_type="automation",
        resource_id=str(automation_id),
        details=f"Deleted automation '{automation_name}'",
    )