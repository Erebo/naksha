"""Initial Schema for NAKSHA Spatial & Land Intelligence Engine

Revision ID: 2026_01_01_0001
Revises: 
Create Date: 2026-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '2026_01_01_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Canonical Parcels Table
    op.create_table(
        'canonical_parcels',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('dag_number', sa.String(length=32), nullable=False),
        sa.Column('khatian_number', sa.String(length=32), nullable=False),
        sa.Column('mouza', sa.String(length=128), nullable=False),
        sa.Column('jl_number', sa.String(length=32), nullable=True),
        sa.Column('upazila', sa.String(length=128), nullable=True),
        sa.Column('district', sa.String(length=128), nullable=True),
        sa.Column('area_decimals', sa.Float(), nullable=False),
        sa.Column('geometry_geojson', sa.Text(), nullable=False),
        sa.Column('geometry_wkt', sa.Text(), nullable=True),
        sa.Column('survey_era', sa.String(length=32), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_canonical_parcels_id', 'canonical_parcels', ['id'], unique=False)
    op.create_index('ix_canonical_parcels_dag_number', 'canonical_parcels', ['dag_number'], unique=False)
    op.create_index('ix_canonical_parcels_khatian_number', 'canonical_parcels', ['khatian_number'], unique=False)
    op.create_index('ix_canonical_parcels_mouza', 'canonical_parcels', ['mouza'], unique=False)

    # 2. Survey History Layers Table
    op.create_table(
        'survey_history_layers',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('parcel_id', sa.String(length=64), nullable=False),
        sa.Column('survey_era', sa.String(length=32), nullable=False),
        sa.Column('layer_type', sa.String(length=64), nullable=False),
        sa.Column('layer_name', sa.String(length=256), nullable=False),
        sa.Column('geometry_geojson', sa.Text(), nullable=False),
        sa.Column('geometry_wkt', sa.Text(), nullable=True),
        sa.Column('area_decimals', sa.Float(), nullable=True),
        sa.Column('properties_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['parcel_id'], ['canonical_parcels.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_survey_history_layers_id', 'survey_history_layers', ['id'], unique=False)
    op.create_index('ix_survey_history_layers_parcel_id', 'survey_history_layers', ['parcel_id'], unique=False)

    # 3. Agency Records Table
    op.create_table(
        'agency_records',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('agency', sa.String(length=64), nullable=False),
        sa.Column('document_type', sa.String(length=128), nullable=False),
        sa.Column('source_record_id', sa.String(length=64), nullable=False),
        sa.Column('canonical_parcel_id', sa.String(length=64), nullable=True),
        sa.Column('dag_number', sa.String(length=32), nullable=True),
        sa.Column('khatian_number', sa.String(length=32), nullable=True),
        sa.Column('mouza', sa.String(length=128), nullable=True),
        sa.Column('owner_name', sa.String(length=256), nullable=True),
        sa.Column('area_decimals', sa.Float(), nullable=True),
        sa.Column('land_class', sa.String(length=64), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('payload_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agency_records_id', 'agency_records', ['id'], unique=False)
    op.create_index('ix_agency_records_agency', 'agency_records', ['agency'], unique=False)
    op.create_index('ix_agency_records_dag_number', 'agency_records', ['dag_number'], unique=False)
    op.create_index('ix_agency_records_khatian_number', 'agency_records', ['khatian_number'], unique=False)
    op.create_index('ix_agency_records_source_record_id', 'agency_records', ['source_record_id'], unique=False)

    # 4. Audit Ledger Entries Table
    op.create_table(
        'audit_ledger_entries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entry_index', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.String(length=64), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('canonical_parcel_id', sa.String(length=64), nullable=True),
        sa.Column('dag_number', sa.String(length=32), nullable=True),
        sa.Column('mouza', sa.String(length=128), nullable=True),
        sa.Column('officer_id', sa.String(length=64), nullable=True),
        sa.Column('verdict', sa.String(length=32), nullable=True),
        sa.Column('cited_records_json', sa.Text(), nullable=True),
        sa.Column('payload_hash', sa.String(length=64), nullable=False),
        sa.Column('previous_hash', sa.String(length=64), nullable=False),
        sa.Column('entry_hash', sa.String(length=64), nullable=False),
        sa.Column('signature_ed25519', sa.String(length=128), nullable=False),
        sa.Column('public_key_ed25519', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entry_hash'),
        sa.UniqueConstraint('entry_index')
    )
    op.create_index('ix_audit_ledger_entries_entry_index', 'audit_ledger_entries', ['entry_index'], unique=True)
    op.create_index('ix_audit_ledger_entries_dag_number', 'audit_ledger_entries', ['dag_number'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_ledger_entries')
    op.drop_table('agency_records')
    op.drop_table('survey_history_layers')
    op.drop_table('canonical_parcels')
