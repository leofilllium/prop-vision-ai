"""
FastAPI application entry point.

Initializes the FastAPI app with CORS, middleware, route mounting,
and lifespan management for database and Redis connections.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as aioredis
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.database import init_db
from app.api.routes import properties, search, comfort, reconstruction, analytics, video, auth, admin
from app.api.middleware import RequestLoggingMiddleware
from app.tasks.uybor_sync import sync_uybor_listings

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("propvision")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    logger.info("Starting PropVision.AI API server...")

    # Initialize database extensions
    await init_db()
    logger.info("Database initialized with PostGIS extension")

    # Initialize Redis connection pool
    app.state.redis = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        max_connections=50,
    )
    logger.info("Redis connection pool created")

    # Start Background Task Scheduler
    scheduler = AsyncIOScheduler()
    if settings.uybor_sync_enabled:
        # Run daily at 04:00 UTC
        scheduler.add_job(
            sync_uybor_listings,
            "cron",
            hour=4,
            minute=0,
            id="uybor_daily_sync",
            replace_existing=True,
        )
        logger.info("Scheduled uybor_daily_sync cron job for 04:00 UTC")

    scheduler.start()
    app.state.scheduler = scheduler

    yield

    # Cleanup
    scheduler.shutdown()
    logger.info("Background scheduler stopped")

    await app.state.redis.close()
    logger.info("Redis connection closed")
    logger.info("PropVision.AI API server stopped")


app = FastAPI(
    redirect_slashes=False,
    title="PropVision.AI API",
    description=(
        "B2B visualization and AI intelligence layer for real estate platforms. "
        "Provides property ingestion, AI-powered search, comfort analytics, "
        "3D reconstruction management, and engagement metrics."
    ),
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

# Custom Request Logging Middleware
app.add_middleware(RequestLoggingMiddleware)

# Mount API routes
app.include_router(
    properties.router,
    prefix="/api/v1/properties",
    tags=["Properties"],
)
app.include_router(
    search.router,
    prefix="/api/v1/search",
    tags=["Search"],
)
app.include_router(
    comfort.router,
    prefix="/api/v1/comfort",
    tags=["Comfort Analytics"],
)
app.include_router(
    reconstruction.router,
    prefix="/api/v1/3d",
    tags=["3D Reconstruction"],
)
app.include_router(
    analytics.router,
    prefix="/api/v1/analytics",
    tags=["Analytics"],
)
app.include_router(
    video.router,
    prefix="/api/v1/video",
    tags=["Video Walkthrough"],
)
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Auth"],
)
app.include_router(
    admin.router,
    prefix="/api/v1/admin",
    tags=["Admin"],
)


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Docker and load balancer probes."""
    return {
        "status": "healthy",
        "service": "propvision-api",
        "version": "1.0.0",
    }
