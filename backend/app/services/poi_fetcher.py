"""
POI (Point of Interest) fetcher service.

Fetches POI data from OpenStreetMap Overpass API and Google Places API,
stores in the pois table for comfort score computation.
"""

import logging
import uuid

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from geoalchemy2.functions import ST_SetSRID, ST_MakePoint
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.models.poi import POI
from app.config import get_settings

logger = logging.getLogger("propvision.services.poi_fetcher")
settings = get_settings()

# Tashkent bounding box (approximate)
TASHKENT_BBOX = {
    "south": 41.20,
    "west": 69.10,
    "north": 41.40,
    "east": 69.40,
}

# OSM Overpass API query settings
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Logical groups for POI fetching to avoid 504 Gateway Timeouts
QUERY_GROUPS = [
    {
        "name": "Infrastructure",
        "tags": [
            'node["highway"="bus_stop"]',
            'node["railway"="subway_station"]',
        ],
    },
    {
        "name": "Amenities",
        "tags": [
            'node["amenity"="school"]',
            'node["amenity"="kindergarten"]',
            'node["amenity"="university"]',
            'node["amenity"="hospital"]',
            'node["amenity"="clinic"]',
            'node["amenity"="pharmacy"]',
            'node["amenity"="police"]',
            'node["amenity"="marketplace"]',
            'node["shop"="supermarket"]',
            'node["shop"="convenience"]',
            'node["amenity"="taxi"]',
        ],
    },
    {
        "name": "Entertainment",
        "tags": [
            'node["amenity"="cinema"]',
            'node["amenity"="theatre"]',
            'node["leisure"="sports_centre"]',
            'way["leisure"="sports_centre"]',
        ],
    },
    {
        "name": "Leisure",
        "tags": [
            'node["leisure"="park"]',
            'way["leisure"="park"]',
            'node["leisure"="garden"]',
            'node["leisure"="playground"]',
        ],
    },
    {
        "name": "Lighting (High Density)",
        "tags": [
            'node["highway"="street_lamp"]',
        ],
    },
]

# Mapping of OSM tags to our categories
OSM_CATEGORY_MAP = {
    ("highway", "bus_stop"): "bus_stop",
    ("railway", "subway_station"): "metro_station",
    ("amenity", "school"): "school",
    ("amenity", "kindergarten"): "kindergarten",
    ("amenity", "university"): "university",
    ("amenity", "hospital"): "hospital",
    ("amenity", "clinic"): "clinic",
    ("amenity", "pharmacy"): "pharmacy",
    ("amenity", "police"): "police_station",
    ("leisure", "park"): "park",
    ("leisure", "garden"): "garden",
    ("leisure", "playground"): "recreation",
    ("leisure", "sports_centre"): "sports_centre",
    ("highway", "street_lamp"): "street_lamp",
    ("amenity", "marketplace"): "market",
    ("shop", "supermarket"): "supermarket",
    ("shop", "convenience"): "convenience_store",
    ("amenity", "cinema"): "cinema",
    ("amenity", "theatre"): "theatre",
    ("amenity", "taxi"): "taxi_stand",
}


class POIFetcherService:
    """Service for fetching POI data from OSM and Google Places."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @retry(
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def _fetch_overpass_group(self, group_name: str, tags: List[str]) -> List[Dict[str, Any]]:
        """Fetch a specific group of tags from Overpass API with retry logic."""
        bbox = TASHKENT_BBOX
        bbox_str = f"({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']})"

        # Build query for the current group
        tag_queries = "\n".join([f"{tag}{bbox_str};" for tag in tags])
        overpass_query = f"""
        [out:json][timeout:180];
        (
          {tag_queries}
        );
        out center;
        """

        logger.info(f"Fetching Overpass group: {group_name}...")
        async with httpx.AsyncClient(timeout=240) as client:
            response = await client.post(
                OVERPASS_URL,
                data={"data": overpass_query},
            )
            if response.status_code == 429:
                logger.warning("Overpass API rate limit (429) hit, retrying...")
                response.raise_for_status()
            elif response.status_code >= 500:
                logger.warning(f"Overpass API server error ({response.status_code}), retrying...")
                response.raise_for_status()

            response.raise_for_status()
            data = response.json()
            return data.get("elements", [])

    async def fetch_osm_pois(self) -> int:
        """
        Fetch POIs from OSM Overpass API for the Tashkent area.
        Uses logical grouping and retries to handle potential timeouts.
        """
        total_stored = 0
        total_fetched = 0

        for group in QUERY_GROUPS:
            try:
                elements = await self._fetch_overpass_group(group["name"], group["tags"])
                total_fetched += len(elements)
                logger.info(f"Group '{group['name']}': fetched {len(elements)} elements")

                if not elements:
                    continue

                # Prepare for bulk upsert
                pois_to_insert = []
                for element in elements:
                    lat = element.get("lat") or element.get("center", {}).get("lat")
                    lon = element.get("lon") or element.get("center", {}).get("lon")
                    if not lat or not lon:
                        continue

                    tags = element.get("tags", {})
                    name = tags.get("name", tags.get("name:en", None))
                    source_id = str(element.get("id"))

                    category = None
                    for (tag_key, tag_value), cat in OSM_CATEGORY_MAP.items():
                        if tags.get(tag_key) == tag_value:
                            category = cat
                            break

                    if not category:
                        continue

                    # Prep POI dict for bulk insertion
                    pois_to_insert.append(
                        {
                            "name": name,
                            "category": category,
                            "location": func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326),
                            "source": "osm",
                            "source_id": source_id,
                            "metadata_": tags,  # Use attribute name to avoid conflict with MetaData
                        }
                    )

                # Perform bulk UPSERT in batches to stay within PostgreSQL's
                # 65535 parameter limit (8 params/row → max ~8191 rows/batch)
                BATCH_SIZE = 1000
                if pois_to_insert:
                    for i in range(0, len(pois_to_insert), BATCH_SIZE):
                        batch = pois_to_insert[i : i + BATCH_SIZE]
                        stmt = pg_insert(POI.__table__).values(
                            [
                                {
                                    "id": uuid.uuid4(),
                                    "name": p["name"],
                                    "category": p["category"],
                                    "location": p["location"],
                                    "source": p["source"],
                                    "source_id": p["source_id"],
                                    "metadata": p["metadata_"],
                                }
                                for p in batch
                            ]
                        )
                        stmt = stmt.on_conflict_do_nothing(index_elements=["source", "source_id"])
                        await self.db.execute(stmt)

                    logger.info(f"Group '{group['name']}': bulk processed {len(pois_to_insert)} POIs")
                    total_stored += len(pois_to_insert)

            except Exception as e:
                logger.error(f"Failed to process Overpass group '{group['name']}': {e}")
                import traceback

                logger.error(traceback.format_exc())
                continue

        await self.db.commit()
        logger.info(f"OSM Fetch Complete: Fetched {total_fetched} total, stored/updated approx {total_stored} POIs")
        return total_stored

    async def fetch_google_places_pois(
        self,
        lat: float = 41.2995,
        lng: float = 69.2401,
        radius: int = 15000,
    ) -> int:
        """
        Fetch POIs from Google Places API Nearby Search.

        Respects the 200 requests/day free tier budget.
        Returns the number of POIs fetched and stored.
        """
        if not settings.google_places_api_key:
            logger.warning("Google Places API key not configured, skipping")
            return 0

        total_stored = 0
        search_types = [
            ("supermarket", "supermarket"),
            ("convenience_store", "convenience_store"),
            ("school", "school"),
            ("university", "university"),
            ("restaurant", "restaurant"),
        ]

        async with httpx.AsyncClient(timeout=30) as client:
            for place_type, category in search_types:
                url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                params = {
                    "location": f"{lat},{lng}",
                    "radius": radius,
                    "type": place_type,
                    "key": settings.google_places_api_key,
                }

                response = await client.get(url, params=params)
                if response.status_code != 200:
                    logger.warning(f"Google Places API error for {place_type}: " f"{response.status_code}")
                    continue

                data = response.json()
                results = data.get("results", [])

                for place in results:
                    location = place.get("geometry", {}).get("location", {})
                    place_lat = location.get("lat")
                    place_lng = location.get("lng")
                    if not place_lat or not place_lng:
                        continue

                    source_id = place.get("place_id")
                    name = place.get("name")

                    # Check for existing
                    existing = await self.db.execute(
                        select(POI).where(
                            POI.source == "google_places",
                            POI.source_id == source_id,
                        )
                    )
                    if existing.scalar_one_or_none() is None:
                        poi = POI(
                            name=name,
                            category=category,
                            location=ST_SetSRID(ST_MakePoint(place_lng, place_lat), 4326),
                            source="google_places",
                            source_id=source_id,
                            metadata_={
                                "rating": place.get("rating"),
                                "vicinity": place.get("vicinity"),
                            },
                        )
                        self.db.add(poi)
                        total_stored += 1

                logger.info(f"Fetched {len(results)} {place_type} from Google Places")

        await self.db.flush()
        logger.info(f"Stored {total_stored} new POIs from Google Places")
        return total_stored
