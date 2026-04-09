"""
Pydantic schemas for analytics dashboard responses.
"""

from pydantic import BaseModel


class DailyApiCalls(BaseModel):
    """API call count for a single day."""

    date: str
    count: int


class TopQuery(BaseModel):
    """Popular search query with count."""

    query: str
    count: int


class DistrictComfortScore(BaseModel):
    """Average comfort score for a district."""

    district: str
    avg_overall_score: float


class Model3DViews(BaseModel):
    """3D model view statistics."""

    total: int
    last_7_days: int


class ApiCallsData(BaseModel):
    """API call statistics."""

    daily: list[DailyApiCalls]
    total_last_30_days: int


class AmenityDemand(BaseModel):
    """Popular amenities requested in AI search."""

    amenity: str
    count: int


class DistrictQueryStats(BaseModel):
    """District search frequency."""

    district: str
    search_count: int


class UserBudgetStats(BaseModel):
    """Averages for user price filters."""

    avg_min_price: float
    avg_max_price: float


class MarketIntelligence(BaseModel):
    """Consumer demand insights from AI search."""

    amenity_demand: list[AmenityDemand]
    district_popularity: list[DistrictQueryStats]
    average_budget: UserBudgetStats


class ComfortPriceEfficiency(BaseModel):
    """District-level value for money (low price, high comfort)."""

    district: str
    efficiency_gap: float  # (avg_comfort / avg_price) * scalar


class InventoryInsights(BaseModel):
    """Backend inventory quality metrics."""

    comfort_price_efficiency: list[ComfortPriceEfficiency]
    spatial_conversion_lift: float  # Estimated lift from 3D views


class ProximityHotspot(BaseModel):
    """Highly requested geographical targets."""

    name: str
    mentions: int


class DashboardResponse(BaseModel):
    """Complete analytics dashboard data."""

    api_calls: ApiCallsData
    top_queries: list[TopQuery]
    comfort_scores_by_district: list[DistrictComfortScore]
    model_3d_views: Model3DViews
    market_intelligence: MarketIntelligence
    inventory_insights: InventoryInsights
    geo_hotspots: list[ProximityHotspot]
