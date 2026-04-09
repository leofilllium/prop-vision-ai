"""add video walkthrough columns

Revision ID: d8f1e2a3b4c5
Revises: c5c71adf0304
Create Date: 2026-04-01 15:38:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8f1e2a3b4c5'
down_revision: Union[str, None] = 'c5c71adf0304'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('properties', sa.Column('video_walkthrough_url', sa.String(500), nullable=True))
    op.add_column('properties', sa.Column('video_generation_status', sa.String(20), nullable=True))
    op.add_column('properties', sa.Column('video_generation_job_id', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('properties', 'video_generation_job_id')
    op.drop_column('properties', 'video_generation_status')
    op.drop_column('properties', 'video_walkthrough_url')
