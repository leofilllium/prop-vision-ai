"""
Comfort analytics computation service.

Computes transport, shopping, education, green space, and safety scores
for each property using PostGIS spatial queries against the POI database.
"""

import json
import logging
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from redis.asyncio import Redis

from app.models.property import Property
from app.models.comfort import ComfortScore
from app.models.poi import POI
from app.schemas.comfort import (
    ComfortScoreDetail,
    ComfortScores,
    ScoreDetails,
    ComfortWeights,
)
from app.config import get_settings

logger = logging.getLogger("propvision.services.comfort")
settings = get_settings()

# Scoring configuration
SCORE_CONFIG = {
    "transport": {
        "categories": ["metro_station", "bus_stop", "taxi_stand"],
        "radius_m": 1000,
        "max_count": 15,
        "weight_nearest": 0.4,
        "weight_density": 0.6,
    },
    "shopping": {
        "categories": ["supermarket", "convenience_store", "market"],
        "radius_m": 800,
        "max_count": 10,
        "weight_nearest": 0.4,
        "weight_density": 0.6,
    },
    "education": {
        "categories": ["school", "kindergarten", "university"],
        "radius_m": 1500,
        "max_count": 8,
        "weight_nearest": 0.4,
        "weight_density": 0.6,
    },
    "green_space": {
        "categories": ["park", "garden", "recreation"],
        "radius_m": 1000,
        "max_count": 5,
        "weight_nearest": 0.5,
        "weight_density": 0.5,
    },
    "safety": {
        "categories": ["police_station", "hospital", "street_lamp"],
        "radius_m": 1000,
        "max_count": 20,
        "weight_nearest": 0.3,
        "weight_density": 0.7,
    },
    "healthcare": {
        "categories": ["hospital", "clinic", "pharmacy"],
        "radius_m": 1500,
        "max_count": 5,
        "weight_nearest": 0.6,
        "weight_density": 0.4,
    },
    "entertainment": {
        "categories": ["cinema", "theatre", "sports_centre"],
        "radius_m": 2000,
        "max_count": 5,
        "weight_nearest": 0.5,
        "weight_density": 0.5,
    },
}


class ComfortService:
    """Service for computing and retrieving comfort analytics scores."""

    def __init__(self, db: AsyncSession, redis: Optional[Redis] = None):
        self.db = db
        self.redis = redis

    async def get_comfort_scores(self, property_id: uuid.UUID) -> Optional[ComfortScoreDetail]:
        """
        Get comfort scores for a property, with Redis caching.

        Cache key: comfort:{property_id}, TTL: 24 hours.
        """
        cache_key = f"comfort:{property_id}"

        # Check Redis cache
        if self.redis:
            cached = await self.redis.get(cache_key)
            if cached:
                data = json.loads(cached)
                return ComfortScoreDetail(**data)

        # Query database
        result = await self.db.execute(select(ComfortScore).where(ComfortScore.property_id == property_id))
        score = result.scalar_one_or_none()

        if score is None:
            return None

        # Build detailed response
        raw = score.raw_data or {}
        weights = settings.comfort_weights

        detail = ComfortScoreDetail(
            property_id=property_id,
            scores=ComfortScores(
                transport=ScoreDetails(
                    score=float(score.transport_score or 0),
                    details=raw.get("transport", {}),
                ),
                shopping=ScoreDetails(
                    score=float(score.shopping_score or 0),
                    details=raw.get("shopping", {}),
                ),
                education=ScoreDetails(
                    score=float(score.education_score or 0),
                    details=raw.get("education", {}),
                ),
                green_space=ScoreDetails(
                    score=float(score.green_space_score or 0),
                    details=raw.get("green_space", {}),
                ),
                safety=ScoreDetails(
                    score=float(score.safety_score or 0),
                    details=raw.get("safety", {}),
                ),
                healthcare=ScoreDetails(
                    score=float(score.healthcare_score or 0),
                    details=raw.get("healthcare", {}),
                ),
                entertainment=ScoreDetails(
                    score=float(score.entertainment_score or 0),
                    details=raw.get("entertainment", {}),
                ),
            ),
            overall_score=float(score.overall_score or 0),
            data_confidence=score.data_confidence,
            weights=ComfortWeights(**weights),
            computed_at=score.computed_at,
        )

        # Cache in Redis (24 hour TTL)
        if self.redis:
            await self.redis.set(
                cache_key,
                detail.model_dump_json(),
                ex=86400,
            )

        return detail

    async def compute_score_for_property(self, property_id: uuid.UUID) -> ComfortScore:
        """
        Compute all comfort scores for a single property.

        For each dimension (transport, shopping, education, green_space, safety, healthcare, entertainment):
        1. Find all POIs of the relevant categories within the scoring radius
        2. Count the number of POIs (density score)
        3. Find the distance to the nearest POI (proximity score)
        4. Combine density and proximity scores with configurable weights
        5. Scale to 0–100 range
        """
        # Get property location
        result = await self.db.execute(select(Property).where(Property.id == property_id))
        prop = result.scalar_one_or_none()
        if not prop:
            raise ValueError(f"Property {property_id} not found")

        scores = {}
        raw_data = {}
        total_data_points = 0

        for dimension, config in SCORE_CONFIG.items():
            dim_score, dim_details, dim_count = await self._compute_dimension(prop.location, config)
            scores[dimension] = dim_score
            raw_data[dimension] = dim_details
            total_data_points += dim_count

        # Compute overall weighted score
        weights = settings.comfort_weights
        overall = sum(scores[dim] * weights[dim] for dim in scores)

        # Determine confidence level
        if total_data_points >= 15:
            confidence = "HIGH"
        elif total_data_points >= 5:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        # Upsert comfort score
        existing = await self.db.execute(select(ComfortScore).where(ComfortScore.property_id == property_id))
        comfort = existing.scalar_one_or_none()

        if comfort is None:
            comfort = ComfortScore(property_id=property_id)
            self.db.add(comfort)

        comfort.transport_score = scores["transport"]
        comfort.shopping_score = scores["shopping"]
        comfort.education_score = scores["education"]
        comfort.green_space_score = scores["green_space"]
        comfort.safety_score = scores["safety"]
        comfort.healthcare_score = scores.get("healthcare", 0.0)
        comfort.entertainment_score = scores.get("entertainment", 0.0)
        comfort.overall_score = round(overall, 2)
        comfort.data_confidence = confidence
        comfort.raw_data = raw_data

        await self.db.flush()
        logger.info(
            f"Computed comfort scores for property {property_id}: " f"overall={overall:.1f}, confidence={confidence}"
        )
        return comfort

    async def _compute_dimension(
        self,
        property_location,
        config: dict,
    ) -> tuple[float, dict, int]:
        """
        Compute a single comfort dimension score.

        Returns: (score 0-100, details dict, data point count)
        """
        categories = config["categories"]
        radius = config["radius_m"]
        max_count = config["max_count"]

        # Find POIs within radius using ST_DWithin with geography cast
        poi_query = (
            select(
                POI.category,
                POI.name,
                func.ST_Distance(
                    func.ST_Transform(property_location, 3857),
                    func.ST_Transform(POI.location, 3857),
                ).label("distance_m"),
            )
            .where(
                POI.category.in_(categories),
                func.ST_DWithin(
                    func.ST_Transform(property_location, 3857),
                    func.ST_Transform(POI.location, 3857),
                    radius,
                ),
            )
            .order_by(text("distance_m ASC"))
        )

        result = await self.db.execute(poi_query)
        pois = result.all()

        count = len(pois)
        nearest_distance = pois[0].distance_m if pois else None

        # Details for raw_data
        details = {}
        top_pois = []
        for cat in categories:
            cat_pois = [p for p in pois if p.category == cat]
            details[f"{cat}s_within_{radius}m"] = len(cat_pois)
            if cat_pois:
                details[f"nearest_{cat}_distance_m"] = round(cat_pois[0].distance_m, 0)

        # Add closest POIs list for frontend display (top 3 overall in this dimension)
        for i, p in enumerate(pois[:3]):
            top_pois.append(
                {
                    "name": p.name or f"Unnamed {p.category.replace('_', ' ').title()}",
                    "category": p.category,
                    "distance_m": round(p.distance_m, 0),
                }
            )
        details["closest_pois"] = top_pois

        # Density score: proportion of max expected POIs (capped at 100)
        density_score = min(100, (count / max_count) * 100)

        # Proximity score: inverse of nearest distance (closer = higher)
        if nearest_distance is not None and nearest_distance > 0:
            proximity_score = max(0, 100 * (1 - nearest_distance / radius))
        else:
            proximity_score = 0 if nearest_distance is None else 100

        # Weighted combination
        w_nearest = config["weight_nearest"]
        w_density = config["weight_density"]
        score = round(proximity_score * w_nearest + density_score * w_density, 2)

        return score, details, count
