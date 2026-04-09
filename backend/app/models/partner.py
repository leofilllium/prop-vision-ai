"""
Partner SQLAlchemy model for B2B API key management.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class Partner(Base):
    """Partner platform with API key and field mapping configuration."""

    __tablename__ = "partners"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    field_mapping = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    properties = relationship("Property", back_populates="partner", lazy="select")

    __table_args__ = (Index("idx_partners_api_key_hash", "api_key_hash"),)

    def __repr__(self) -> str:
        return f"<Partner(id={self.id}, name='{self.name}')>"
