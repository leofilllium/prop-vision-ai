"""
Uybor.uz Marketplace scraper service.

Fetches up to 50 for-sale USD apartment listings from api.uybor.uz in a
single request (no pagination), transforms them into Property-compatible
records, and upserts into the database using external_id for deduplication.

Coordinate resolution order:
  1. Use lat/lng from the Uybor API response directly (most listings have them).
  2. If lat/lng are null or zero, call Google Geocoding API to resolve the
     address string → coordinates.
  3. Skip the listing only if both attempts fail.
"""

import logging
from typing import Any, Optional

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_SetSRID, ST_MakePoint

from app.config import get_settings
from app.models.property import Property

logger = logging.getLogger("propvision.services.uybor_scraper")
settings = get_settings()

# Fixed query parameters — do not change
UYBOR_PARAMS: dict[str, Any] = {
    "mode": "search",
    "includeFeatured": "true",
    "limit": 50,
    "embed": (
        "category,subCategory,residentialComplex,region,city,district,"
        "zone,street,metro,media,user,user.avatar,user.organization,"
        "user.organization.logo"
    ),
    "order": "createdAt",
    "operationType__eq": "sale",
    "priceCurrency__eq": "usd",
    "category__eq": 7,  # Apartment
}

UYBOR_HEADERS = {
    "accept": "*/*",
    "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "origin": "https://uybor.uz",
    "referer": "https://uybor.uz/",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.0.0 Safari/537.36"
    ),
}

GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


class UyborScraperService:
    """Scrapes Uybor.uz marketplace and syncs apartment data into Property table."""

    def __init__(self, db: AsyncSession, partner_id: str):
        self.db = db
        self.partner_id = partner_id

    # ------------------------------------------------------------------
    # Fetch
    # ------------------------------------------------------------------

    async def fetch_listings(self) -> list[dict[str, Any]]:
        """Fetch the first 50 listings from Uybor.uz in a single call."""
        async with httpx.AsyncClient(timeout=60, headers=UYBOR_HEADERS, verify=False) as client:
            try:
                response = await client.get(
                    settings.uybor_api_base_url,
                    params=UYBOR_PARAMS,
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                logger.error(f"Uybor API request failed: {type(e).__name__}: {e}")
                return []

        payload = response.json()
        results = payload.get("results", [])
        logger.info(f"Uybor API returned {len(results)} listings " f"(total available: {payload.get('total', '?')})")
        return results

    # ------------------------------------------------------------------
    # Geocoding fallback
    # ------------------------------------------------------------------

    async def _geocode_address(self, address: str, district: Optional[str]) -> Optional[tuple[float, float]]:
        """
        Call Google Geocoding API to resolve a place name to (lat, lng).
        Builds query: "<address>, <district>, Tashkent, Uzbekistan"
        Returns (lat, lng) tuple or None on failure.
        """
        if not settings.google_places_api_key:
            logger.warning("Google Places API key not configured — cannot geocode.")
            return None

        parts = [p for p in [address, district, "Tashkent", "Uzbekistan"] if p]
        query = ", ".join(parts)

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(
                    GOOGLE_GEOCODE_URL,
                    params={"address": query, "key": settings.google_places_api_key},
                )
                resp.raise_for_status()
                data = resp.json()
                if data.get("status") == "OK" and data.get("results"):
                    loc = data["results"][0]["geometry"]["location"]
                    return float(loc["lat"]), float(loc["lng"])
                logger.warning(f"Geocoding returned status '{data.get('status')}' for query: {query}")
            except Exception as e:
                logger.warning(f"Geocoding failed for '{query}': {e}")

        return None

    # ------------------------------------------------------------------
    # Mapping
    # ------------------------------------------------------------------

    async def map_to_properties(self, listings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Transform raw Uybor listing dicts into Property-ready dicts.
        Resolves coordinates, falling back to Google Geocoding where needed.
        """
        properties: list[dict[str, Any]] = []

        for item in listings:
            listing_id = item.get("id")

            # Skip inactive or non-approved listings
            if not item.get("isActive", True):
                continue
            if item.get("moderationStatus") != "approved":
                continue

            # --- Coordinates ---
            lat = item.get("lat")
            lng = item.get("lng")

            if not lat or not lng or lat == 0 or lng == 0:
                # Attempt geocoding fallback
                address_str = item.get("address", "")
                district_obj = item.get("district") or {}
                district_name = (
                    district_obj.get("name", {}).get("en") if isinstance(district_obj.get("name"), dict) else None
                )
                result = await self._geocode_address(address_str, district_name)
                if result is None:
                    logger.warning(f"Skipping listing {listing_id}: " f"no coordinates and geocoding failed")
                    continue
                lat, lng = result

            # --- District ---
            district_obj = item.get("district") or {}
            district_name = None
            if isinstance(district_obj.get("name"), dict):
                district_name = district_obj["name"].get("en") or district_obj["name"].get("ru") or None

            # --- Category / title ---
            category_obj = item.get("category") or {}
            category_en = "Apartment"
            if isinstance(category_obj.get("name"), dict):
                category_en = category_obj["name"].get("en", "Apartment")

            rooms_raw = item.get("room")
            rooms = int(rooms_raw) if rooms_raw and str(rooms_raw).isdigit() else None

            address_str = item.get("address") or ""
            title = f"{category_en}"
            if rooms:
                title += f" {rooms}BR"
            if address_str:
                title += f" — {address_str}"

            # --- Photos ---
            photos = [
                m["url"].replace("/media/n/", "/media/o/")
                for m in (item.get("media") or [])
                if isinstance(m, dict) and m.get("url")
            ]

            # --- Price ---
            price = item.get("price")
            if not price:
                logger.debug(f"Skipping listing {listing_id}: missing price")
                continue

            properties.append(
                {
                    "external_id": f"uybor-{listing_id}",
                    "title": title[:500],
                    "description": (item.get("description") or "")[:5000] or None,
                    "price": float(price),
                    "currency": (item.get("priceCurrency") or "usd").upper(),
                    "rooms": rooms,
                    "area_sqm": float(item["square"]) if item.get("square") else None,
                    "floor": item.get("floor"),
                    "total_floors": item.get("floorTotal"),
                    "district": district_name,
                    "address": address_str or None,
                    "lat": float(lat),
                    "lng": float(lng),
                    "photos": photos,
                    "is_new_building": item.get("isNewBuilding", False),
                }
            )

        logger.info(f"Mapped {len(properties)} valid properties from {len(listings)} listings")
        return properties

    # ------------------------------------------------------------------
    # Upsert
    # ------------------------------------------------------------------

    async def sync(self) -> dict[str, int]:
        """
        Full sync: fetch → map → upsert.

        On conflict (same external_id + partner_id):
          - UPDATE price, area, title, description, district, address, lat, lng, floor, total_floors
          - DO NOT update photos (preserve existing imagery)
          - DO NOT update model_3d_url or reconstruction_status

        Returns dict with created/updated counts.
        """
        listings = await self.fetch_listings()
        mapped = await self.map_to_properties(listings)

        created = 0
        updated = 0

        for prop_data in mapped:
            external_id = prop_data["external_id"]

            # Check if already exists
            result = await self.db.execute(
                select(Property).where(
                    Property.external_id == external_id,
                    Property.partner_id == self.partner_id,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update core fields only — preserve photos and 3D model
                await self.db.execute(
                    update(Property)
                    .where(Property.id == existing.id)
                    .values(
                        title=prop_data["title"],
                        description=prop_data["description"],
                        price=prop_data["price"],
                        currency=prop_data["currency"],
                        rooms=prop_data["rooms"],
                        area_sqm=prop_data["area_sqm"],
                        floor=prop_data["floor"],
                        total_floors=prop_data["total_floors"],
                        district=prop_data["district"],
                        address=prop_data["address"],
                        lat=prop_data["lat"],
                        lng=prop_data["lng"],
                        location=ST_SetSRID(
                            ST_MakePoint(prop_data["lng"], prop_data["lat"]),
                            4326,
                        ),
                    )
                )
                updated += 1
            else:
                # Insert new property
                new_prop = Property(
                    title=prop_data["title"],
                    description=prop_data["description"],
                    price=prop_data["price"],
                    currency=prop_data["currency"],
                    rooms=prop_data["rooms"],
                    area_sqm=prop_data["area_sqm"],
                    floor=prop_data["floor"],
                    total_floors=prop_data["total_floors"],
                    district=prop_data["district"],
                    address=prop_data["address"],
                    lat=prop_data["lat"],
                    lng=prop_data["lng"],
                    location=ST_SetSRID(
                        ST_MakePoint(prop_data["lng"], prop_data["lat"]),
                        4326,
                    ),
                    photos=prop_data["photos"],
                    partner_id=self.partner_id,
                    external_id=external_id,
                    is_active=True,
                )
                self.db.add(new_prop)
                created += 1

        await self.db.flush()

        logger.info(f"Uybor sync complete: {created} created, {updated} updated")
        return {"created": created, "updated": updated}
