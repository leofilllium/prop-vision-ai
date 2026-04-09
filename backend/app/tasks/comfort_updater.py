"""
Nightly comfort score recomputation task.

Triggered by cron job (01:00 UTC daily). Iterates through all active
properties and recomputes their comfort scores using the latest POI data.
"""

import asyncio
import logging
from datetime import datetime, timezone

from app.database import async_session_factory
from app.models.property import Property
from app.services.comfort_service import ComfortService
from sqlalchemy import select

logger = logging.getLogger("propvision.tasks.comfort_updater")


async def recompute_all_comfort_scores() -> None:
    """
    Recompute comfort scores for all active properties.

    This task is designed to run as a nightly cron job. It iterates
    through all active properties and computes fresh comfort scores
    using the latest POI data in the database.
    """
    start_time = datetime.now(timezone.utc)
    logger.info("Starting nightly comfort score recomputation...")

    async with async_session_factory() as db:
        # Get all active properties
        result = await db.execute(select(Property.id).where(Property.is_active == True))  # noqa
        property_ids = [row[0] for row in result.all()]

        logger.info(f"Found {len(property_ids)} active properties to process")

        service = ComfortService(db)
        success_count = 0
        error_count = 0

        for prop_id in property_ids:
            try:
                await service.compute_score_for_property(prop_id)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to compute comfort scores for {prop_id}: {e}")
                error_count += 1

        await db.commit()

    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info(
        f"Comfort score recomputation complete. "
        f"Success: {success_count}, Errors: {error_count}, "
        f"Duration: {elapsed:.1f}s"
    )


def run_comfort_updater():
    """Entry point for the cron job."""
    asyncio.run(recompute_all_comfort_scores())


if __name__ == "__main__":
    run_comfort_updater()
