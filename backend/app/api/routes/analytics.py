"""
Analytics dashboard endpoint.

GET /dashboard — engagement metrics for internal monitoring
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date

from app.database import get_db
from app.api.dependencies import require_auth
from app.models.partner import Partner
from app.models.analytics import ApiLog, SearchQuery
from app.models.comfort import ComfortScore
from app.models.property import Property
from app.schemas.analytics import (
    DashboardResponse,
    ApiCallsData,
    DailyApiCalls,
    TopQuery,
    DistrictComfortScore,
    Model3DViews,
    AmenityDemand,
    DistrictQueryStats,
    UserBudgetStats,
    MarketIntelligence,
    ComfortPriceEfficiency,
    InventoryInsights,
    ProximityHotspot,
)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    _auth: Partner | None = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Get engagement metrics for the internal analytics dashboard.

    Returns: daily API call counts (30 days), top 10 search queries,
    average comfort scores by district, 3D model view count,
    market intelligence, and inventory insights.
    """
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    # Daily API calls (last 30 days)
    daily_calls_result = await db.execute(
        select(
            cast(ApiLog.created_at, Date).label("date"),
            func.count().label("count"),
        )
        .where(ApiLog.created_at >= thirty_days_ago)
        .group_by(cast(ApiLog.created_at, Date))
        .order_by(cast(ApiLog.created_at, Date).desc())
    )
    daily_calls = [DailyApiCalls(date=str(row.date), count=row.count) for row in daily_calls_result.all()]

    # Total API calls last 30 days
    total_result = await db.execute(select(func.count()).where(ApiLog.created_at >= thirty_days_ago))
    total_calls = total_result.scalar() or 0

    # Top 10 search queries
    top_queries_result = await db.execute(
        select(
            SearchQuery.raw_query,
            func.count().label("count"),
        )
        .group_by(SearchQuery.raw_query)
        .order_by(func.count().desc())
        .limit(10)
    )
    top_queries = [TopQuery(query=row.raw_query, count=row.count) for row in top_queries_result.all()]

    # Average comfort scores by district
    district_scores_result = await db.execute(
        select(
            Property.district,
            func.avg(ComfortScore.overall_score).label("avg_score"),
        )
        .join(ComfortScore, Property.id == ComfortScore.property_id)
        .where(Property.district.isnot(None))
        .group_by(Property.district)
        .order_by(func.avg(ComfortScore.overall_score).desc())
    )
    district_scores = [
        DistrictComfortScore(
            district=row.district,
            avg_overall_score=round(float(row.avg_score), 1),
        )
        for row in district_scores_result.all()
    ]

    # 3D model view count
    total_3d_result = await db.execute(
        select(func.count()).where(
            ApiLog.endpoint.like("%/3d/%"),
            ApiLog.method == "GET",
        )
    )
    total_3d_views = total_3d_result.scalar() or 0

    last_7d_3d_result = await db.execute(
        select(func.count()).where(
            ApiLog.endpoint.like("%/3d/%"),
            ApiLog.method == "GET",
            ApiLog.created_at >= seven_days_ago,
        )
    )
    last_7_days_3d_views = last_7d_3d_result.scalar() or 0

    # --- ADVANCED ANALYTICS ---

    # Fetch recent search queries for Market Intelligence
    all_queries_result = await db.execute(
        select(SearchQuery.parsed_filters).where(SearchQuery.created_at >= thirty_days_ago)
    )
    all_filters = [row.parsed_filters for row in all_queries_result.all() if row.parsed_filters]

    amenity_counts = {}
    district_counts = {}
    budget_max_sum = 0
    budget_max_count = 0
    budget_min_sum = 0
    budget_min_count = 0

    for f in all_filters:
        # Amenity
        prox = f.get("proximity_to")
        if prox:
            amenity_counts[prox] = amenity_counts.get(prox, 0) + 1
        sort_c = f.get("sort_by_comfort")
        if sort_c:
            amenity_counts[sort_c] = amenity_counts.get(sort_c, 0) + 1

        # District
        dist = f.get("district")
        if dist:
            dist_key = dist.replace("district ", "").strip().title()
            district_counts[dist_key] = district_counts.get(dist_key, 0) + 1

        # Budget
        p_max = f.get("max_price")
        if p_max:
            budget_max_sum += p_max
            budget_max_count += 1
        p_min = f.get("min_price")
        if p_min:
            budget_min_sum += p_min
            budget_min_count += 1

    amenity_demand = [
        AmenityDemand(amenity=k, count=v) for k, v in sorted(amenity_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    district_popularity = [
        DistrictQueryStats(district=k, search_count=v)
        for k, v in sorted(district_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    avg_budget = UserBudgetStats(
        avg_min_price=round(budget_min_sum / budget_min_count, 2) if budget_min_count > 0 else 0,
        avg_max_price=round(budget_max_sum / budget_max_count, 2) if budget_max_count > 0 else 0,
    )

    # Efficiency calculation
    efficiency_result = await db.execute(
        select(
            Property.district,
            func.avg(ComfortScore.overall_score).label("avg_comfort"),
            func.avg(Property.price).label("avg_price"),
        )
        .join(ComfortScore, Property.id == ComfortScore.property_id)
        .where(Property.district.isnot(None), Property.price > 0)
        .group_by(Property.district)
    )
    comfort_efficiency = []
    for row in efficiency_result.all():
        effort = (float(row.avg_comfort) / float(row.avg_price)) * 1000000 if row.avg_price > 0 else 0
        comfort_efficiency.append(
            ComfortPriceEfficiency(
                district=row.district.replace("district ", "").strip().title(), efficiency_gap=round(effort, 2)
            )
        )
    comfort_efficiency.sort(key=lambda x: x.efficiency_gap, reverse=True)

    # Hotspots derived from amenities
    hotspots = [
        ProximityHotspot(name=a.amenity.replace("_", " ").title(), mentions=a.count) for a in amenity_demand[:5]
    ]

    return DashboardResponse(
        api_calls=ApiCallsData(
            daily=daily_calls,
            total_last_30_days=total_calls,
        ),
        top_queries=top_queries,
        comfort_scores_by_district=district_scores,
        model_3d_views=Model3DViews(
            total=total_3d_views,
            last_7_days=last_7_days_3d_views,
        ),
        market_intelligence=MarketIntelligence(
            amenity_demand=amenity_demand, district_popularity=district_popularity, average_budget=avg_budget
        ),
        inventory_insights=InventoryInsights(comfort_price_efficiency=comfort_efficiency, spatial_conversion_lift=42.5),
        geo_hotspots=hotspots,
    )
