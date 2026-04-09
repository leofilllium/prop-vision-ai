"""
Pydantic v2 schemas for property request/response validation.
Handles GeoJSON serialization from PostGIS WKB elements.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Any
from datetime import datetime
from uuid import UUID


class GeoJSONPoint(BaseModel):
    """GeoJSON Point geometry."""

    type: str = "Point"
    coordinates: list[float] = Field(..., description="[longitude, latitude]", min_length=2, max_length=2)


class ComfortScoreBrief(BaseModel):
    """Abbreviated comfort score for property list views."""

    transport_score: float | None = None
    shopping_score: float | None = None
    education_score: float | None = None
    green_space_score: float | None = None
    safety_score: float | None = None
    healthcare_score: float | None = None
    entertainment_score: float | None = None
    overall_score: float | None = None
    data_confidence: str = "MEDIUM"


class PropertyCreate(BaseModel):
    """Schema for creating a new property listing via partner API."""

    title: str = Field(..., max_length=500)
    description: str | None = None
    price: float = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    rooms: int | None = Field(default=None, ge=1)
    area_sqm: float | None = Field(default=None, ge=0)
    floor: int | None = None
    total_floors: int | None = None
    district: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=500)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    photos: list[str] = Field(default_factory=list)
    external_id: str | None = None


class PropertyResponse(BaseModel):
    """Full property response schema with comfort scores."""

    id: UUID
    title: str
    description: str | None = None
    price: float
    currency: str = "USD"
    rooms: int | None = None
    area_sqm: float | None = None
    floor: int | None = None
    total_floors: int | None = None
    district: str | None = None
    address: str | None = None
    location: GeoJSONPoint
    photos: list[str] = []
    model_3d_url: str | None = None
    comfort_score: ComfortScoreBrief | None = None
    partner_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def convert_geometry(cls, data: Any) -> Any:
        """Convert GeoAlchemy2 WKBElement to GeoJSON Point."""
        if hasattr(data, "__dict__"):
            # SQLAlchemy model instance
            from shapely import wkb

            obj_dict = {}
            for key in [
                "id",
                "title",
                "description",
                "price",
                "currency",
                "rooms",
                "area_sqm",
                "floor",
                "total_floors",
                "district",
                "address",
                "photos",
                "model_3d_url",
                "partner_id",
                "created_at",
                "updated_at",
            ]:
                obj_dict[key] = getattr(data, key, None)

            # Convert geometry
            location = getattr(data, "location", None)
            if location is not None:
                try:
                    point = wkb.loads(bytes(location.data))
                    obj_dict["location"] = {
                        "type": "Point",
                        "coordinates": [point.x, point.y],
                    }
                except Exception:
                    obj_dict["location"] = {"type": "Point", "coordinates": [0, 0]}
            else:
                obj_dict["location"] = {"type": "Point", "coordinates": [0, 0]}

            # Convert comfort score
            cs = getattr(data, "comfort_score", None)
            if cs is not None:
                obj_dict["comfort_score"] = {
                    "transport_score": float(cs.transport_score) if cs.transport_score else None,
                    "shopping_score": float(cs.shopping_score) if cs.shopping_score else None,
                    "education_score": float(cs.education_score) if cs.education_score else None,
                    "green_space_score": float(cs.green_space_score) if cs.green_space_score else None,
                    "safety_score": float(cs.safety_score) if cs.safety_score else None,
                    "healthcare_score": float(cs.healthcare_score) if cs.healthcare_score else None,
                    "entertainment_score": float(cs.entertainment_score) if cs.entertainment_score else None,
                    "overall_score": float(cs.overall_score) if cs.overall_score else None,
                    "data_confidence": cs.data_confidence or "MEDIUM",
                }

            return obj_dict
        return data


class PropertyBrief(BaseModel):
    """Brief property info for search results with distance."""

    id: UUID
    title: str
    price: float
    rooms: int | None = None
    area_sqm: float | None = None
    district: str | None = None
    location: GeoJSONPoint
    photos: list[str] = []
    comfort_score: ComfortScoreBrief | None = None
    distance_to_poi_m: float | None = None

    model_config = {"from_attributes": True}


class PropertyListResponse(BaseModel):
    """Paginated property list response."""

    total: int
    limit: int
    offset: int
    results: list[PropertyResponse]
