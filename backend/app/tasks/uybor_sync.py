"""
Daily Uybor.uz marketplace data synchronization task.

Triggered by APScheduler cron (daily at 04:00 UTC). Fetches the first 50
for-sale USD apartment listings from Uybor.uz and upserts them into the
database using external_id for deduplication.
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import async_session_factory
from app.models.partner import Partner
from app.services.uybor_scraper import UyborScraperService

logger = logging.getLogger("propvision.tasks.uybor_sync")

UYBOR_PARTNER_NAME = "Uybor Marketplace"


async def sync_uybor_listings() -> None:
    """
    Fetch and sync property listings from Uybor.uz marketplace.

    This task runs daily to keep our property database up to date
    with the latest prices and availability from Uybor.uz.
    Only the first 50 results are fetched per run — no pagination.
    """
    start_time = datetime.now(timezone.utc)
    logger.info("Starting daily Uybor.uz marketplace sync...")

    async with async_session_factory() as db:
        # Find the Uybor partner record created by migration
        result = await db.execute(select(Partner).where(Partner.name == UYBOR_PARTNER_NAME))
        partner = result.scalar_one_or_none()

        if not partner:
            logger.error(
                f"Partner '{UYBOR_PARTNER_NAME}' not found in database. "
                "Run `alembic upgrade head` to apply the migration."
            )
            return

        service = UyborScraperService(db, partner_id=partner.id)

        try:
            stats = await service.sync()
            await db.commit()
            logger.info(f"Uybor sync successful: " f"{stats['created']} new, {stats['updated']} updated")
        except Exception as e:
            await db.rollback()
            logger.error(f"Uybor sync failed: {e}", exc_info=True)

    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info(f"Uybor sync duration: {elapsed:.1f}s")


def run_uybor_sync():
    """Entry point for manual / CLI execution."""
    asyncio.run(sync_uybor_listings())


if __name__ == "__main__":
    run_uybor_sync()
