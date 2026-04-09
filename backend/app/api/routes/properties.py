"""
Property CRUD API endpoints.

POST / — create property (partner ingestion)
GET / — list/filter properties with spatial queries
GET /{id} — single property with comfort scores
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.dependencies import check_rate_limit, require_auth
from app.models.partner import Partner
from app.schemas.property import (
    PropertyCreate,
    PropertyResponse,
    PropertyListResponse,
)
from app.services.property_service import PropertyService

router = APIRouter()


@router.post("", response_model=PropertyResponse, status_code=201)
async def create_property(
    property_data: PropertyCreate,
    partner: Partner = Depends(check_rate_limit),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new property listing.

    Partners push property data through this endpoint. Fields are mapped
    using the partner's field_mapping configuration stored in the database.
    """
    service = PropertyService(db)
    try:
        prop = await service.create_property(property_data, partner.id)
        return PropertyResponse.model_validate(prop)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("", response_model=PropertyListResponse)
async def list_properties(
    district: str | None = Query(default=None, description="Filter by district"),
    min_price: float | None = Query(default=None, ge=0, description="Minimum price"),
    max_price: float | None = Query(default=None, ge=0, description="Maximum price"),
    rooms: int | None = Query(default=None, ge=1, description="Exact room count"),
    min_rooms: int | None = Query(default=None, ge=1, description="Minimum rooms"),
    max_rooms: int | None = Query(default=None, ge=1, description="Maximum rooms"),
    bbox: str | None = Query(
        default=None,
        description="Bounding box: sw_lng,sw_lat,ne_lng,ne_lat",
    ),
    limit: int = Query(default=50, ge=1, le=100, description="Max results"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    sort_by: str = Query(
        default="created_at",
        description="Sort field",
        pattern="^(price|rooms|created_at)$",
    ),
    sort_order: str = Query(
        default="desc",
        description="Sort order",
        pattern="^(asc|desc)$",
    ),
    _auth: Partner | None = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    List and filter properties.

    Supports spatial bounding box, price range, room count, and district filters.
    Results are paginated with configurable limit and offset.
    """
    service = PropertyService(db)

    # Parse bounding box
    bbox_coords = None
    if bbox:
        try:
            parts = [float(x) for x in bbox.split(",")]
            if len(parts) != 4:
                raise ValueError()
            bbox_coords = tuple(parts)
        except (ValueError, IndexError):
            raise HTTPException(
                status_code=422,
                detail="Invalid bbox format. Expected: sw_lng,sw_lat,ne_lng,ne_lat",
            )

    properties, total = await service.list_properties(
        district=district,
        min_price=min_price,
        max_price=max_price,
        rooms=rooms,
        min_rooms=min_rooms,
        max_rooms=max_rooms,
        bbox=bbox_coords,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    results = [PropertyResponse.model_validate(p) for p in properties]
    return PropertyListResponse(
        total=total,
        limit=limit,
        offset=offset,
        results=results,
    )


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: UUID,
    _auth: Partner | None = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get a single property with full comfort scores."""
    service = PropertyService(db)
    prop = await service.get_property(property_id)

    if prop is None:
        raise HTTPException(status_code=404, detail="Property not found")

    return PropertyResponse.model_validate(prop)
