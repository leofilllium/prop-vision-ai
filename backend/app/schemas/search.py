"""
Pydantic schemas for AI search request and response.
"""

from pydantic import BaseModel, Field
from typing import Optional

from app.schemas.property import PropertyResponse


class ParsedFilters(BaseModel):
    """Structured filters extracted from natural language query by AI."""

    rooms: Optional[int] = Field(default=None, description="Exact room count")
    min_price: Optional[float] = Field(default=None, description="Minimum price in USD")
    max_price: Optional[float] = Field(default=None, description="Maximum price in USD")
    district: Optional[str] = Field(default=None, description="District or neighborhood name")
    proximity_to: Optional[str] = Field(
        default=None,
        description="POI type to be near: metro_station, park, school, supermarket, hospital",
    )
    max_distance_m: Optional[int] = Field(default=None, description="Maximum distance to POI in meters")
    min_area_sqm: Optional[float] = Field(default=None, description="Minimum area in square meters")
    max_area_sqm: Optional[float] = Field(default=None, description="Maximum area in square meters")
    sort_by_comfort: Optional[str] = Field(
        default=None,
        description=(
            "Comfort category to sort by (e.g. transport, shopping, "
            "education, green_space, safety, healthcare, entertainment)"
        ),
    )


class SearchRequest(BaseModel):
    """AI search request body."""

    query: str = Field(
        ...,
        max_length=500,
        description="Natural language property search query",
        examples=["2-room flat near metro under $70,000"],
    )


class SearchResponse(BaseModel):
    """AI search response with parsed filters and matching properties."""

    query: str
    parsed_filters: ParsedFilters
    total: int
    results: list[PropertyResponse]
