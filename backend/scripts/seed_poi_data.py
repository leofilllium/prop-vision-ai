"""
Seed real Tashkent POI data from OpenStreetMap Overpass API using a single
optimized query to prevent rate limiting (429s) and speed up the process.

Run:
    docker exec propvision-api python -m scripts.seed_poi_data
"""

import asyncio
import logging
import uuid
import httpx
from geoalchemy2.functions import ST_SetSRID, ST_MakePoint
from app.database import async_session_factory, init_db
from app.models.poi import POI

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("seed_poi")

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
# Expanded bounding box to cover the entire Tashkent Metro area including outer districts (Sergeli, Bektemir, Uchtepa)
BBOX = "41.10,69.10,41.45,69.50"

# All necessary tags mapped to our DB categories
TAG_MAPPINGS = [
    # Transport
    ({"railway": "subway_station"}, "metro_station"),
    ({"station": "subway"}, "metro_station"),
    ({"highway": "bus_stop"}, "bus_stop"),
    ({"highway": "tram_stop"}, "bus_stop"), # count trams as buses for score
    ({"amenity": "taxi"}, "taxi_stand"),
    
    # Shopping
    ({"shop": "supermarket"}, "supermarket"),
    ({"shop": "hypermarket"}, "supermarket"),
    ({"shop": "convenience"}, "convenience_store"),
    ({"shop": "grocery"}, "convenience_store"),
    ({"shop": "kiosk"}, "convenience_store"),
    ({"shop": "bakery"}, "convenience_store"),
    ({"shop": "butcher"}, "convenience_store"),
    ({"shop": "greengrocer"}, "convenience_store"),
    ({"amenity": "marketplace"}, "market"),
    ({"shop": "mall"}, "market"),
    
    # Education
    ({"amenity": "school"}, "school"),
    ({"amenity": "language_school"}, "school"),
    ({"amenity": "kindergarten"}, "kindergarten"),
    ({"amenity": "university"}, "university"),
    ({"amenity": "college"}, "university"),
    
    # Healthcare
    ({"amenity": "hospital"}, "hospital"),
    ({"amenity": "clinic"}, "clinic"),
    ({"amenity": "dentist"}, "clinic"),
    ({"amenity": "pharmacy"}, "pharmacy"),
    
    # Green Space
    ({"leisure": "park"}, "park"),
    ({"natural": "wood"}, "park"),
    ({"leisure": "nature_reserve"}, "park"),
    ({"leisure": "garden"}, "garden"),
    ({"leisure": "playground"}, "recreation"),
    ({"landuse": "recreation_ground"}, "recreation"),
    
    # Entertainment
    ({"amenity": "cinema"}, "cinema"),
    ({"amenity": "theatre"}, "theatre"),
    ({"leisure": "sports_centre"}, "sports_centre"),
    ({"amenity": "cafe"}, "sports_centre"),  # Proxy mapped for density
    ({"amenity": "restaurant"}, "sports_centre"), # Proxy mapped for density
    
    # Safety
    ({"amenity": "police"}, "police_station"),
    ({"highway": "street_lamp"}, "street_lamp"),
]

def build_query() -> str:
    queries = []
    for tags, _ in TAG_MAPPINGS:
        k, v = list(tags.items())[0]
        # We query nodes for everything to keep it fast
        queries.append(f'  node["{k}"="{v}"]({BBOX});')
    
    q_str = "\n".join(queries)
    return f"""[out:json][timeout:180];
(
{q_str}
);
out center;"""

def match_category(element_tags: dict) -> str | None:
    for mapping_tags, category in TAG_MAPPINGS:
        k, v = list(mapping_tags.items())[0]
        if element_tags.get(k) == v:
            return category
    return None

def _get_coords(element: dict) -> tuple[float, float] | None:
    lat = element.get("lat") or element.get("center", {}).get("lat")
    lon = element.get("lon") or element.get("center", {}).get("lon")
    if lat and lon:
        return float(lat), float(lon)
    return None

def _get_name(tags: dict) -> str | None:
    return tags.get("name:en") or tags.get("name:ru") or tags.get("name") or None

async def seed_pois():
    await init_db()
    
    logger.info("Starting single-pass OSM fetch...")
    query = build_query()
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(OVERPASS_URL, data={"data": query}, timeout=180)
            resp.raise_for_status()
            data = resp.json()
            elements = data.get("elements", [])
            logger.info(f"Successfully fetched {len(elements)} combined POIs from OSM.")
        except Exception as e:
            logger.error(f"Failed to fetch from Overpass: {e}")
            return
            
    if not elements:
        logger.warning("No elements returned from OSM!")
        return

    pois_to_insert = []
    for el in elements:
        coords = _get_coords(el)
        if not coords: continue
        
        tags = el.get("tags", {})
        category = match_category(tags)
        if not category: continue
        
        pois_to_insert.append({
            "id": uuid.uuid4(),
            "name": _get_name(tags),
            "category": category,
            "location": ST_SetSRID(ST_MakePoint(coords[1], coords[0]), 4326),
            "source": "osm",
            "source_id": str(el.get("id", "")),
            "metadata": tags,
        })

    logger.info(f"Mapped {len(pois_to_insert)} POIs. Inserting into database in batches...")

    async with async_session_factory() as db:
        BATCH = 1000
        for i in range(0, len(pois_to_insert), BATCH):
            batch = pois_to_insert[i:i+BATCH]
            for p in batch:
                db.add(POI(**p))
            await db.commit()
            logger.info(f"  Saved {i + len(batch)} / {len(pois_to_insert)}")

    logger.info("✅ Single-pass POI seed complete.")

if __name__ == "__main__":
    asyncio.run(seed_pois())
