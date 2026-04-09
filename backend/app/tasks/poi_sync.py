"""
Periodic POI data synchronization task.

Triggered by cron job (Sunday 03:00 UTC weekly). Fetches fresh POI data
from OSM Overpass API and Google Places API.
"""

import asyncio
import logging
from datetime import datetime, timezone

from app.database import async_session_factory
from app.services.poi_fetcher import POIFetcherService

logger = logging.getLogger("propvision.tasks.poi_sync")


async def sync_all_pois() -> None:
    """
    Fetch and sync POI data from all external sources.

    This task runs weekly to refresh the POI database with latest data
    from OpenStreetMap and Google Places.
    """
    start_time = datetime.now(timezone.utc)
    logger.info("Starting weekly POI data synchronization...")

    async with async_session_factory() as db:
        service = POIFetcherService(db)

        # Fetch from OSM
        try:
            osm_count = await service.fetch_osm_pois()
            logger.info(f"OSM sync: {osm_count} new POIs stored")
        except Exception as e:
            logger.error(f"OSM sync failed: {e}")
            osm_count = 0

        # Fetch from Google Places
        try:
            google_count = await service.fetch_google_places_pois()
            logger.info(f"Google Places sync: {google_count} new POIs stored")
        except Exception as e:
            logger.error(f"Google Places sync failed: {e}")
            google_count = 0

        await db.commit()

    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info(
        f"POI sync complete. "
        f"New OSM POIs: {osm_count}, New Google POIs: {google_count}, "
        f"Duration: {elapsed:.1f}s"
    )


def run_poi_sync():
    """Entry point for the cron job."""
    asyncio.run(sync_all_pois())


if __name__ == "__main__":
    run_poi_sync()
