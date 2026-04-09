"""
AI-powered natural language search endpoint.

POST / — parse natural language query and return matching properties
"""

import time
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.dependencies import require_auth
from app.models.partner import Partner
from app.schemas.search import SearchRequest, SearchResponse
from app.schemas.property import PropertyResponse
from app.services.ai_search_service import AISearchService

logger = logging.getLogger("propvision.search")
router = APIRouter()


@router.post("", response_model=SearchResponse)
async def ai_search(
    request: SearchRequest,
    _auth: Partner | None = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    AI-powered natural language property search.

    Accepts a free-form text query, uses OpenAI GPT-4o-mini to parse it into
    structured filters, then executes a PostGIS spatial query to find matching
    properties. The AI only translates language into database queries — it does
    not hallucinate listings.

    Supported query patterns:
    - Room count: "2 rooms", "3-room", "3 xonali", "двухкомнатная"
    - Price range: "under $70k", "до 80 тысяч", "50 ming dollar"
    - District: "Yunusabad", "Chilanzar", "Чиланзар"
    - Proximity: "near metro", "close to a park", "metro yaqinida"
    - Area: "80 square meters", "80 m²"
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=422,
            detail="Search query cannot be empty",
        )

    start_time = time.time()
    service = AISearchService(db)

    try:
        parsed_filters, properties = await service.search(request.query)
    except ValueError as e:
        logger.warning(f"Failed to parse query: {request.query!r} — {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Could not parse your search query: {e}",
        )
    except Exception as e:
        logger.error(f"Search error for query {request.query!r}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your search",
        )

    processing_time_ms = int((time.time() - start_time) * 1000)

    # Log the query for analytics
    await service.log_search_query(
        raw_query=request.query,
        parsed_filters=parsed_filters.model_dump(),
        result_count=len(properties),
        processing_time_ms=processing_time_ms,
    )

    results = [PropertyResponse.model_validate(p) for p in properties]

    return SearchResponse(
        query=request.query,
        parsed_filters=parsed_filters,
        total=len(results),
        results=results,
    )
