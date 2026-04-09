"""add users table

Revision ID: e1f2a3b4c5d6
Revises: d8f1e2a3b4c5
Create Date: 2026-04-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'e1f2a3b4c5d6'
down_revision = 'd8f1e2a3b4c5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='viewer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('idx_users_email', 'users', ['email'])


def downgrade() -> None:
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
