"""Service endpoints (tenant-scoped CRUD)."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import (
    require_business_owner,
    require_business_staff_or_owner,
    require_membership,
)
from app.core.database import get_db
from app.models.business import Business
from app.models.product import Service
from app.models.user import BusinessUser, User
from app.schemas.common import PaginatedResponse
from app.schemas.product import ServiceCreate, ServiceOut, ServiceUpdate

router = APIRouter(prefix="/services", tags=["services"])


def _images_to_str(images: list[str]) -> str:
    """Convert a list of image URLs to the JSON storage format."""
    import json

    return json.dumps(images)


def _images_from_str(images: str) -> list[str]:
    """Convert the JSON storage format to a list."""
    import json

    if not images:
        return []
    try:
        parsed = json.loads(images)
        return parsed if isinstance(parsed, list) else []
    except (ValueError, TypeError):
        return []


def _service_out(service: Service) -> ServiceOut:
    """Build a ServiceOut with images converted to a list."""
    return ServiceOut(
        id=service.id,
        business_id=service.business_id,
        name=service.name,
        description=service.description,
        price=service.price,
        currency=service.currency,
        duration=service.duration,
        category=service.category,
        availability=service.availability,
        images=_images_from_str(service.images),
        location=service.location,
        additional_info=service.additional_info,
        is_active=service.is_active,
        created_at=service.created_at,
        updated_at=service.updated_at,
    )


def _get_service_or_404(db: Session, business_id: int, service_id: int) -> Service:
    """Fetch a service that belongs to the given business or raise 404."""
    service = (
        db.query(Service)
        .filter(Service.id == service_id, Service.business_id == business_id)
        .first()
    )
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )
    return service


@router.get("/", response_model=PaginatedResponse[ServiceOut])
def list_services(
    search: str | None = Query(default=None, description="Search by name or category"),
    category: str | None = Query(default=None, description="Filter by category"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ServiceOut]:
    """List services for the current business only."""
    _, _, business = ctx
    query = db.query(Service).filter(Service.business_id == business.id)

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(Service.name.ilike(like), Service.category.ilike(like))
        )
    if category:
        query = query.filter(Service.category == category)

    total = query.count()
    services = (
        query.order_by(Service.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedResponse[ServiceOut](
        items=[_service_out(s) for s in services],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/",
    response_model=ServiceOut,
    status_code=status.HTTP_201_CREATED,
)
def create_service(
    payload: ServiceCreate,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_staff_or_owner),
    db: Session = Depends(get_db),
) -> ServiceOut:
    """Create a service in the current business."""
    _, _, business = ctx
    service = Service(
        business_id=business.id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        currency=payload.currency,
        duration=payload.duration,
        category=payload.category,
        availability=payload.availability,
        images=_images_to_str(payload.images),
        location=payload.location,
        additional_info=payload.additional_info,
        is_active=payload.is_active,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return _service_out(service)


@router.get("/{service_id}", response_model=ServiceOut)
def get_service(
    service_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> ServiceOut:
    """Return a single service if it belongs to the current business."""
    _, _, business = ctx
    service = _get_service_or_404(db, business.id, service_id)
    return _service_out(service)


@router.patch("/{service_id}", response_model=ServiceOut)
def update_service(
    service_id: int,
    payload: ServiceUpdate,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_staff_or_owner),
    db: Session = Depends(get_db),
) -> ServiceOut:
    """Update a service in the current business."""
    _, _, business = ctx
    service = _get_service_or_404(db, business.id, service_id)

    data = payload.model_dump(exclude_unset=True)
    if "images" in data and data["images"] is not None:
        data["images"] = _images_to_str(data["images"])
    for field, value in data.items():
        if value is not None:
            setattr(service, field, value)

    db.commit()
    db.refresh(service)
    return _service_out(service)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_owner),
    db: Session = Depends(get_db),
) -> None:
    """Delete a service. Owner-only."""
    _, _, business = ctx
    service = _get_service_or_404(db, business.id, service_id)
    db.delete(service)
    db.commit()