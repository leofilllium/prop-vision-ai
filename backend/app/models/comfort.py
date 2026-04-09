"""
ComfortScore SQLAlchemy model for location-based livability scores.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Numeric, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class ComfortScore(Base):
    """Location-based livability scores for a property."""

    __tablename__ = "comfort_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    transport_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    shopping_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    education_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    green_space_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    safety_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    healthcare_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    entertainment_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    data_confidence: Mapped[str] = mapped_column(String(10), default="MEDIUM")
    raw_data = mapped_column(JSONB, default=dict)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    property = relationship(
        "Property",
        back_populates="comfort_score",
        lazy="select",
    )

    __table_args__ = (
        Index("idx_comfort_property", "property_id"),
        Index("idx_comfort_overall", "overall_score"),
    )

    def __repr__(self) -> str:
        return (
            f"<ComfortScore(property_id={self.property_id}, "
            f"overall={self.overall_score}, confidence={self.data_confidence})>"
        )
