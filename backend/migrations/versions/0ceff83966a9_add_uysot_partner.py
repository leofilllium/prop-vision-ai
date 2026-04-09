"""add uysot partner

Revision ID: 0ceff83966a9
Revises: v1_initial_schema
Create Date: 2026-03-29 00:52:59.767597

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ceff83966a9'
down_revision: Union[str, None] = 'v1_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    import uuid
    # Add Uysot Marketplace partner
    op.execute(
        f"""
        INSERT INTO partners (id, name, api_key_hash, is_active, field_mapping, created_at, updated_at)
        SELECT '{uuid.uuid4()}', 'Uysot Marketplace', 'uysot-internal-scraper-no-auth', true, '{{}}'::jsonb, NOW(), NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM partners WHERE name = 'Uysot Marketplace'
        );
        """
    )


def downgrade() -> None:
    # Remove Uysot Marketplace partner
    op.execute(
        """
        DELETE FROM partners WHERE name = 'Uysot Marketplace';
        """
    )
