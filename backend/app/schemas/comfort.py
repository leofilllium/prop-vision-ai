"""
Pydantic schemas for comfort score responses.
"""

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class ScoreDetails(BaseModel):
    """Detailed breakdown of a single comfort dimension."""

    score: float
    details: dict


class ComfortScores(BaseModel):
    """All five comfort dimensions with details."""

    transport: ScoreDetails
    shopping: ScoreDetails
    education: ScoreDetails
    green_space: ScoreDetails
    safety: ScoreDetails
    healthcare: ScoreDetails
    entertainment: ScoreDetails


class ComfortWeights(BaseModel):
    """Weight configuration for comfort score calculation."""

    transport: float = 0.20
    shopping: float = 0.15
    education: float = 0.15
    green_space: float = 0.10
    safety: float = 0.15
    healthcare: float = 0.15
    entertainment: float = 0.10


class ComfortScoreResponse(BaseModel):
    """Comfort score summary for property list views."""

    overall_score: float | None = None
    data_confidence: str = "MEDIUM"
    computed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ComfortScoreDetail(BaseModel):
    """Full comfort score breakdown with details and weights."""

    property_id: UUID
    scores: ComfortScores
    overall_score: float
    data_confidence: str = "MEDIUM"
    weights: ComfortWeights
    computed_at: datetime

    model_config = {"from_attributes": True}
