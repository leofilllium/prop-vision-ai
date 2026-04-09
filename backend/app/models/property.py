"""
Property SQLAlchemy model with GeoAlchemy2 spatial column.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String,
    Text,
    Numeric,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from geoalchemy2 import Geometry

from app.database import Base


class Property(Base):
    """Real estate property listing with geospatial location."""

    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    rooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area_sqm: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    floor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_floors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    district: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    lat: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    lng: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    location = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
    )
    photos = mapped_column(JSONB, default=list)
    model_3d_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reconstruction_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reconstruction_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    video_walkthrough_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_generation_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    video_generation_job_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partners.id", ondelete="SET NULL"),
        nullable=True,
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
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
    comfort_score = relationship(
        "ComfortScore",
        back_populates="property",
        uselist=False,
        lazy="joined",
    )
    partner = relationship("Partner", back_populates="properties", lazy="select")

    __table_args__ = (
        Index("idx_properties_location", location, postgresql_using="gist"),
        Index("idx_properties_district", "district"),
        Index("idx_properties_price", "price"),
        Index("idx_properties_rooms", "rooms"),
        Index(
            "idx_properties_active",
            "is_active",
            postgresql_where=(is_active == True),  # noqa: E712
        ),
        Index("idx_properties_partner", "partner_id"),
        Index(
            "idx_properties_partner_external",
            "partner_id",
            "external_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<Property(id={self.id}, title='{self.title}', price={self.price})>"
