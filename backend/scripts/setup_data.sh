#!/bin/bash
# PropVision AI - Automated Data Setup Script
# Use this script inside the running 'propvision-api' container.
#
# Usage:
#   docker exec -it propvision-api bash scripts/setup_data.sh

set -e

echo "--------------------------------------------------------"
echo "🚀 PropVision AI: Starting Data Setup"
echo "--------------------------------------------------------"

# 1. Run Migrations
echo "📦 [1/3] Running Database Migrations (Alembic)..."
alembic upgrade head

# Wipe all seed-managed tables so each run starts clean
echo "🧹 Cleaning seed tables (properties, pois, comfort_scores)..."
python - <<'EOF'
import asyncio
from sqlalchemy import text
from app.database import async_session_factory, init_db

async def cleanup():
    await init_db()
    async with async_session_factory() as db:
        await db.execute(text("TRUNCATE TABLE properties, pois, comfort_scores RESTART IDENTITY CASCADE;"))
        await db.commit()
    print("Done.")

asyncio.run(cleanup())
EOF

# 2. Seed POI Data
echo "📍 [2/3] Seeding POI data from OpenStreetMap (Tashkent)..."
# Using -m to ensure package context is preserved
python -m scripts.seed_poi_data

# 3. Sync Marketplace
echo "📊 [3/3] Synchronizing Uybor Marketplace Listings..."
python run_sync.py

echo "--------------------------------------------------------"
echo "✅ Data setup complete! Application is ready."
echo "--------------------------------------------------------"
