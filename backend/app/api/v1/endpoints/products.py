"""Product endpoints (tenant-scoped CRUD)."""
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
from app.models.product import Product
from app.models.user import BusinessUser, User
from app.schemas.common import PaginatedResponse
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


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


def _product_out(product: Product) -> ProductOut:
    """Build a ProductOut with images converted to a list."""
    return ProductOut(
        id=product.id,
        business_id=product.business_id,
        name=product.name,
        description=product.description,
        price=product.price,
        currency=product.currency,
        sku=product.sku,
        category=product.category,
        stock=product.stock,
        availability=product.availability,
        images=_images_from_str(product.images),
        location=product.location,
        additional_info=product.additional_info,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def _get_product_or_404(db: Session, business_id: int, product_id: int) -> Product:
    """Fetch a product that belongs to the given business or raise 404."""
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.business_id == business_id)
        .first()
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


@router.get("/", response_model=PaginatedResponse[ProductOut])
def list_products(
    search: str | None = Query(default=None, description="Search by name, category or SKU"),
    category: str | None = Query(default=None, description="Filter by category"),
    availability: str | None = Query(default=None, description="Filter by availability"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ProductOut]:
    """List products for the current business only."""
    _, _, business = ctx
    query = db.query(Product).filter(Product.business_id == business.id)

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(like),
                Product.category.ilike(like),
                Product.sku.ilike(like),
            )
        )
    if category:
        query = query.filter(Product.category == category)
    if availability:
        query = query.filter(Product.availability == availability)

    total = query.count()
    products = (
        query.order_by(Product.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedResponse[ProductOut](
        items=[_product_out(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    payload: ProductCreate,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_staff_or_owner),
    db: Session = Depends(get_db),
) -> ProductOut:
    """Create a product in the current business."""
    _, _, business = ctx
    product = Product(
        business_id=business.id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        currency=payload.currency,
        sku=payload.sku,
        category=payload.category,
        stock=payload.stock,
        availability=payload.availability,
        images=_images_to_str(payload.images),
        location=payload.location,
        additional_info=payload.additional_info,
        is_active=payload.is_active,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return _product_out(product)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> ProductOut:
    """Return a single product if it belongs to the current business."""
    _, _, business = ctx
    product = _get_product_or_404(db, business.id, product_id)
    return _product_out(product)


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_staff_or_owner),
    db: Session = Depends(get_db),
) -> ProductOut:
    """Update a product in the current business."""
    _, _, business = ctx
    product = _get_product_or_404(db, business.id, product_id)

    data = payload.model_dump(exclude_unset=True)
    if "images" in data and data["images"] is not None:
        data["images"] = _images_to_str(data["images"])
    for field, value in data.items():
        if value is not None:
            setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return _product_out(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_owner),
    db: Session = Depends(get_db),
) -> None:
    """Delete a product. Owner-only."""
    _, _, business = ctx
    product = _get_product_or_404(db, business.id, product_id)
    db.delete(product)
    db.commit()