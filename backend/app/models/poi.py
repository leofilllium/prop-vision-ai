"""
Point of Interest (POI) SQLAlchemy model with geospatial location.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from geoalchemy2 import Geometry

from app.database import Base


class POI(Base):
    """Point of interest sourced from OSM or Google Places."""

    __tablename__ = "pois"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    location = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_ = mapped_column("metadata", JSONB, default=dict)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_pois_location", location, postgresql_using="gist"),
        Index("idx_pois_category", "category"),
        Index("idx_pois_source", "source"),
        Index(
            "idx_pois_source_id",
            "source",
            "source_id",
            unique=True,
            postgresql_where=(source_id.isnot(None)),  # type: ignore
        ),
    )

    def __repr__(self) -> str:
        return f"<POI(name='{self.name}', category='{self.category}', source='{self.source}')>"
