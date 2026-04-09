"""
Property CRUD service with PostGIS spatial queries.
"""

import uuid
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc
from geoalchemy2.functions import ST_MakeEnvelope, ST_MakePoint, ST_SetSRID

from app.models.property import Property
from app.models.comfort import ComfortScore
from app.schemas.property import PropertyCreate

logger = logging.getLogger("propvision.services.property")


class PropertyService:
    """Service for property CRUD operations with spatial queries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_property(
        self,
        data: PropertyCreate,
        partner_id: uuid.UUID,
    ) -> Property:
        """
        Create a new property listing with a PostGIS POINT geometry.

        Converts latitude/longitude to a GEOMETRY(POINT, 4326) using
        ST_SetSRID(ST_MakePoint(lng, lat), 4326).
        """
        # Check for duplicate (partner_id + external_id)
        if data.external_id:
            existing = await self.db.execute(
                select(Property).where(
                    Property.partner_id == partner_id,
                    Property.external_id == data.external_id,
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Property with external_id '{data.external_id}' " f"already exists for this partner")

        prop = Property(
            title=data.title,
            description=data.description,
            price=data.price,
            currency=data.currency,
            rooms=data.rooms,
            area_sqm=data.area_sqm,
            floor=data.floor,
            total_floors=data.total_floors,
            district=data.district,
            address=data.address,
            location=ST_SetSRID(ST_MakePoint(data.longitude, data.latitude), 4326),
            photos=data.photos,
            partner_id=partner_id,
            external_id=data.external_id,
        )

        self.db.add(prop)
        await self.db.flush()
        await self.db.refresh(prop)

        logger.info(f"Created property {prop.id}: {prop.title}")
        return prop

    async def get_property(self, property_id: uuid.UUID) -> Optional[Property]:
        """Get a single property by ID with eager-loaded comfort scores."""
        result = await self.db.execute(
            select(Property)
            .where(Property.id == property_id, Property.is_active == True)  # noqa
            .outerjoin(ComfortScore)
        )
        return result.unique().scalar_one_or_none()

    async def list_properties(
        self,
        district: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        rooms: Optional[int] = None,
        min_rooms: Optional[int] = None,
        max_rooms: Optional[int] = None,
        bbox: Optional[tuple[float, float, float, float]] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Property], int]:
        """
        List properties with filters and spatial bounding box.

        Args:
            bbox: (sw_lng, sw_lat, ne_lng, ne_lat) bounding box for spatial filter
        """
        query = select(Property).where(Property.is_active == True)  # noqa

        # Apply filters
        if district:
            query = query.where(func.lower(Property.district) == func.lower(district))
        if min_price is not None:
            query = query.where(Property.price >= min_price)
        if max_price is not None:
            query = query.where(Property.price <= max_price)
        if rooms is not None:
            query = query.where(Property.rooms == rooms)
        if min_rooms is not None:
            query = query.where(Property.rooms >= min_rooms)
        if max_rooms is not None:
            query = query.where(Property.rooms <= max_rooms)

        # Spatial bounding box filter
        if bbox:
            sw_lng, sw_lat, ne_lng, ne_lat = bbox
            envelope = ST_MakeEnvelope(sw_lng, sw_lat, ne_lng, ne_lat, 4326)
            query = query.where(func.ST_Within(Property.location, envelope))

        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(Property, sort_by, Property.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Join comfort scores for response
        query = query.outerjoin(ComfortScore)

        result = await self.db.execute(query)
        properties = result.unique().scalars().all()

        return list(properties), total
