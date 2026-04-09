"""add uybor partner and lat lng columns

Revision ID: a1b2c3d4e5f6
Revises: 0ceff83966a9
Create Date: 2026-04-01 00:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '0ceff83966a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    import uuid

    # ── Add lat / lng columns for raw coordinate storage ─────────────
    op.add_column('properties', sa.Column('lat', sa.Numeric(precision=10, scale=7), nullable=True))
    op.add_column('properties', sa.Column('lng', sa.Numeric(precision=10, scale=7), nullable=True))

    # ── Insert Uybor Marketplace partner ─────────────────────────────
    op.execute(
        f"""
        INSERT INTO partners (id, name, api_key_hash, is_active, field_mapping, created_at, updated_at)
        SELECT '{uuid.uuid4()}', 'Uybor Marketplace', 'uybor-internal-scraper-no-auth', true, '{{}}'::jsonb, NOW(), NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM partners WHERE name = 'Uybor Marketplace'
        );
        """
    )


def downgrade() -> None:
    # Remove Uybor Marketplace partner (only if no properties are linked)
    op.execute(
        """
        DELETE FROM partners
        WHERE name = 'Uybor Marketplace'
          AND id NOT IN (SELECT DISTINCT partner_id FROM properties WHERE partner_id IS NOT NULL);
        """
    )

    # Drop lat / lng columns
    op.drop_column('properties', 'lng')
    op.drop_column('properties', 'lat')
