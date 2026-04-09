"""
Analytics SQLAlchemy models for API logging and search query tracking.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class ApiLog(Base):
    """API request log for monitoring and analytics."""

    __tablename__ = "api_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partners.id", ondelete="SET NULL"),
        nullable=True,
    )
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_metadata = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_api_logs_partner", "partner_id"),
        Index("idx_api_logs_created", "created_at"),
        Index("idx_api_logs_endpoint", "endpoint"),
    )

    def __repr__(self) -> str:
        return f"<ApiLog(endpoint='{self.endpoint}', method='{self.method}', " f"status={self.status_code})>"


class SearchQuery(Base):
    """Logged AI search query with parsed filters and result count."""

    __tablename__ = "search_queries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    raw_query: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_filters = mapped_column(JSONB, default=dict)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    parse_success: Mapped[bool] = mapped_column(Boolean, default=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (Index("idx_search_queries_created", "created_at"),)

    def __repr__(self) -> str:
        return f"<SearchQuery(query='{self.raw_query[:50]}...', " f"results={self.result_count})>"
