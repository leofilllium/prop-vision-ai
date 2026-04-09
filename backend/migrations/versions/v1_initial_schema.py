"""initial schema

Revision ID: v1_initial_schema
Revises: 
Create Date: 2026-03-28 04:08:12.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision = 'v1_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Create Extension ──────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')

    # ── Partners ──────────────────────────────────
    op.create_table(
        'partners',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('api_key_hash', sa.String(length=64), nullable=False),
        sa.Column('webhook_url', sa.String(length=500), nullable=True),
        sa.Column('field_mapping', postgresql.JSONB(), server_default='{}', nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('api_key_hash')
    )
    op.execute('CREATE INDEX IF NOT EXISTS idx_partners_api_key_hash ON partners (api_key_hash)')

    # ── Properties ────────────────────────────────
    op.create_table(
        'properties',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('rooms', sa.Integer(), nullable=True),
        sa.Column('area_sqm', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('floor', sa.Integer(), nullable=True),
        sa.Column('total_floors', sa.Integer(), nullable=True),
        sa.Column('district', sa.String(length=255), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromText', name='geometry'), nullable=False),
        sa.Column('photos', postgresql.JSONB(), server_default='[]', nullable=True),
        sa.Column('model_3d_url', sa.String(length=500), nullable=True),
        sa.Column('reconstruction_status', sa.String(length=20), nullable=True),
        sa.Column('reconstruction_job_id', sa.String(length=255), nullable=True),
        sa.Column('partner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.execute('CREATE INDEX IF NOT EXISTS idx_properties_location ON properties USING gist (location)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_properties_district ON properties (district)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_properties_price ON properties (price)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_properties_rooms ON properties (rooms)')
    op.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_properties_partner_external ON properties (partner_id, external_id)')

    # ── Comfort Scores ────────────────────────────
    op.create_table(
        'comfort_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('property_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transport_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('shopping_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('education_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('green_space_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('safety_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('overall_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('data_confidence', sa.String(length=10), nullable=False),
        sa.Column('raw_data', postgresql.JSONB(), server_default='{}', nullable=True),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('property_id')
    )
    op.execute('CREATE INDEX IF NOT EXISTS idx_comfort_property ON comfort_scores (property_id)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_comfort_overall ON comfort_scores (overall_score)')

    # ── POIs ──────────────────────────────────────
    op.create_table(
        'pois',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromText', name='geometry'), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('source_id', sa.String(length=255), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}', nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.execute('CREATE INDEX IF NOT EXISTS idx_pois_location ON pois USING gist (location)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_pois_category ON pois (category)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_pois_source ON pois (source)')
    op.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_pois_source_id ON pois (source, source_id) WHERE source_id IS NOT NULL')

    # ── API Logs ──────────────────────────────────
    op.create_table(
        'api_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('partner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('endpoint', sa.String(length=255), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('request_metadata', postgresql.JSONB(), server_default='{}', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.execute('CREATE INDEX IF NOT EXISTS idx_api_logs_partner ON api_logs (partner_id)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_api_logs_created ON api_logs (created_at)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint ON api_logs (endpoint)')

    # ── Search Queries ────────────────────────────
    op.create_table(
        'search_queries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('raw_query', sa.Text(), nullable=False),
        sa.Column('parsed_filters', postgresql.JSONB(), server_default='{}', nullable=True),
        sa.Column('result_count', sa.Integer(), nullable=False),
        sa.Column('parse_success', sa.Boolean(), nullable=False),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.execute('CREATE INDEX IF NOT EXISTS idx_search_queries_created ON search_queries (created_at)')


def downgrade() -> None:
    op.drop_table('search_queries')
    op.drop_table('api_logs')
    op.drop_table('pois')
    op.drop_table('comfort_scores')
    op.drop_table('properties')
    op.drop_table('partners')
