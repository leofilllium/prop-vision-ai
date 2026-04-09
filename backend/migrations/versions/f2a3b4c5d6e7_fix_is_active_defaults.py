"""fix is_active server defaults and backfill

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-04-03 00:00:00.000000

Sets server_default=true on properties.is_active and partners.is_active
so rows inserted outside the ORM are active by default.
Also backfills any existing rows where is_active is false or NULL.
"""
from alembic import op
import sqlalchemy as sa

revision = 'f2a3b4c5d6e7'
down_revision = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Set server_default and backfill properties
    op.alter_column(
        'properties', 'is_active',
        existing_type=sa.Boolean(),
        server_default=sa.text('true'),
        existing_nullable=False,
    )
    op.execute("UPDATE properties SET is_active = true WHERE is_active IS NULL OR is_active = false")

    # Set server_default on partners too (same pattern)
    op.alter_column(
        'partners', 'is_active',
        existing_type=sa.Boolean(),
        server_default=sa.text('true'),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column('properties', 'is_active', existing_type=sa.Boolean(), server_default=None)
    op.alter_column('partners', 'is_active', existing_type=sa.Boolean(), server_default=None)
