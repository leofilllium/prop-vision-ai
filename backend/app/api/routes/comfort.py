"""
Comfort analytics API endpoints.

GET /{property_id} — detailed comfort scores with breakdown.
Scores are computed on-demand if not yet calculated.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.dependencies import require_auth
from app.models.partner import Partner
from app.schemas.comfort import ComfortScoreDetail
from app.services.comfort_service import ComfortService

router = APIRouter()


@router.get("/{property_id}", response_model=ComfortScoreDetail)
async def get_comfort_scores(
    property_id: UUID,
    request: Request,
    _auth: Partner | None = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed comfort score breakdown for a property.

    Returns transport, shopping, education, green space, and safety scores
    (0–100 each) with detailed breakdowns showing POI counts and distances.
    Scores are cached in Redis with a 24-hour TTL.

    If scores have not been computed yet, they are computed on-demand.
    """
    redis = request.app.state.redis
    service = ComfortService(db, redis)

    scores = await service.get_comfort_scores(property_id)

    if scores is None:
        # Compute on-demand — property may not have been processed by nightly task yet
        try:
            await service.compute_score_for_property(property_id)
            await db.commit()
            scores = await service.get_comfort_scores(property_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Property not found")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to compute comfort scores: {e}",
            )

    if scores is None:
        raise HTTPException(
            status_code=404,
            detail="Comfort scores could not be computed for this property.",
        )

    return scores
