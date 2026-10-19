"""PostgreSQL + PostGIS Foundation Schema

Revision ID: 2026_10_19_0002
Revises: 2026_01_01_0001
Create Date: 2026-10-19 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geometry

revision: str = '2026_10_19_0002'
down_revision: Union[str, None] = '2026_01_01_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PROTOTYPE_TABLES = [
    'survey_history_layers',
    'agency_records',
    'audit_ledger_entries',
    'canonical_parcels',
]


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        # Keep SQLite path operational with prototype schema
        return

    # 1. On PostgreSQL: Verify prototype tables are empty before replacing
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    for tbl in PROTOTYPE_TABLES:
        if tbl in existing_tables:
            count = bind.execute(sa.text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
            if count > 0:
                raise RuntimeError(
                    f"Cannot apply PostGIS migration: prototype table '{tbl}' contains {count} existing rows."
                )

    # Drop empty prototype tables in dependency order
    for tbl in PROTOTYPE_TABLES:
        if tbl in existing_tables:
            op.drop_table(tbl)

    # 2. Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # 3. Create Canonical Parcels Table
    op.create_table(
        'canonical_parcels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('mouza', sa.String(length=128), nullable=False),
        sa.Column('dag_number', sa.String(length=32), nullable=False),
        sa.Column('khatian_number', sa.String(length=32), nullable=False),
        sa.Column('jl_number', sa.String(length=32), nullable=True),
        sa.Column('upazila', sa.String(length=128), nullable=True),
        sa.Column('district', sa.String(length=128), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('geometry', Geometry(geometry_type='POLYGON', srid=4326, spatial_index=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('active', 'archived', 'disputed', 'merged', 'subdivided')", name='chk_parcels_status'),
        sa.CheckConstraint("ST_IsValid(geometry)", name='chk_parcels_geometry_valid'),
    )
    op.create_index('ix_canonical_parcels_mouza', 'canonical_parcels', ['mouza'])
    op.create_index('ix_canonical_parcels_dag_number', 'canonical_parcels', ['dag_number'])
    op.create_index('ix_canonical_parcels_khatian_number', 'canonical_parcels', ['khatian_number'])
    op.create_index('ix_canonical_parcels_mouza_dag', 'canonical_parcels', ['mouza', 'dag_number'])

    # 4. Create Agency Records Table
    op.create_table(
        'agency_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('parcel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('canonical_parcels.id', ondelete='SET NULL'), nullable=True),
        sa.Column('agency', sa.String(length=64), nullable=False),
        sa.Column('source_record_id', sa.String(length=128), nullable=False),
        sa.Column('document_type', sa.String(length=64), nullable=False),
        sa.Column('raw_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('normalized_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('extraction_confidence', sa.Float(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('agency', 'source_record_id', name='uq_agency_records_agency_source_record_id'),
        sa.CheckConstraint('extraction_confidence IS NULL OR (extraction_confidence >= 0.0 AND extraction_confidence <= 1.0)', name='chk_agency_records_confidence'),
    )
    op.create_index('ix_agency_records_agency', 'agency_records', ['agency'])
    op.create_index('ix_agency_records_parcel_id', 'agency_records', ['parcel_id'])

    # 5. Create Parcel Lineage Table
    op.create_table(
        'parcel_lineage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('parent_parcel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('canonical_parcels.id', ondelete='CASCADE'), nullable=False),
        sa.Column('child_parcel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('canonical_parcels.id', ondelete='CASCADE'), nullable=False),
        sa.Column('survey_era', sa.String(length=16), nullable=False),
        sa.Column('relation', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('parent_parcel_id != child_parcel_id', name='chk_parcel_lineage_no_self_link'),
        sa.CheckConstraint("survey_era IN ('CS', 'SA', 'RS', 'BS', 'DLRS')", name='chk_parcel_lineage_survey_era'),
        sa.CheckConstraint("relation IN ('subdivision', 'amalgamation', 'succession', 're-survey')", name='chk_parcel_lineage_relation'),
    )
    op.create_index('ix_parcel_lineage_parent', 'parcel_lineage', ['parent_parcel_id'])
    op.create_index('ix_parcel_lineage_child', 'parcel_lineage', ['child_parcel_id'])

    # 6. Create Survey Layers Table
    op.create_table(
        'survey_layers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('parcel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('canonical_parcels.id', ondelete='CASCADE'), nullable=False),
        sa.Column('survey_era', sa.String(length=16), nullable=False),
        sa.Column('layer_type', sa.String(length=64), nullable=False),
        sa.Column('geometry', Geometry(geometry_type='POLYGON', srid=4326, spatial_index=True), nullable=False),
        sa.Column('area_decimals', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("survey_era IN ('CS', 'SA', 'RS', 'BS', 'DLRS')", name='chk_survey_layers_survey_era'),
        sa.CheckConstraint('ST_IsValid(geometry)', name='chk_survey_layers_geometry_valid'),
    )
    op.create_index('ix_survey_layers_parcel_id', 'survey_layers', ['parcel_id'])

    # 7. Create Restricted Zones Table
    op.create_table(
        'restricted_zones',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('zone_type', sa.String(length=64), nullable=False),
        sa.Column('geometry', Geometry(geometry_type='POLYGON', srid=4326, spatial_index=True), nullable=False),
        sa.Column('source', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("zone_type IN ('khas', 'canal', 'river', 'forest', 'wetland', 'railway', 'embankment', 'vested_property')", name='chk_restricted_zones_zone_type'),
        sa.CheckConstraint('ST_IsValid(geometry)', name='chk_restricted_zones_geometry_valid'),
    )

    # 8. Create Officers Table
    op.create_table(
        'officers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('officer_id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('designation', sa.String(length=128), nullable=False),
        sa.Column('role', sa.String(length=64), nullable=False),
        sa.Column('jurisdiction', sa.String(length=128), nullable=False),
        sa.Column('office', sa.String(length=256), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('officer_id', name='uq_officers_officer_id'),
        sa.CheckConstraint("role IN ('ac_land', 'kanungo', 'surveyor', 'sub_registrar', 'dc', 'admin', 'auditor')", name='chk_officers_role'),
    )
    op.create_index('ix_officers_officer_id', 'officers', ['officer_id'])

    # 9. Create Tax Payments Table
    op.create_table(
        'tax_payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('parcel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('canonical_parcels.id', ondelete='CASCADE'), nullable=False),
        sa.Column('fiscal_year', sa.String(length=16), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('payer_name', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('paid', 'unpaid', 'overdue', 'exempt', 'partial')", name='chk_tax_payments_status'),
    )
    op.create_index('ix_tax_payments_parcel_id', 'tax_payments', ['parcel_id'])

    # 10. Create Liens Table
    op.create_table(
        'liens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('parcel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('canonical_parcels.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lien_type', sa.String(length=64), nullable=False),
        sa.Column('holder', sa.String(length=256), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("lien_type IN ('mortgage', 'court_attachment', 'government_charge', 'freeze', 'dispute')", name='chk_liens_lien_type'),
        sa.CheckConstraint("status IN ('active', 'discharged', 'pending', 'cancelled')", name='chk_liens_status'),
    )
    op.create_index('ix_liens_parcel_id', 'liens', ['parcel_id'])


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        return

    # Drop PostGIS tables in reverse order
    op.drop_table('liens')
    op.drop_table('tax_payments')
    op.drop_table('officers')
    op.drop_table('restricted_zones')
    op.drop_table('survey_layers')
    op.drop_table('parcel_lineage')
    op.drop_table('agency_records')
    op.drop_table('canonical_parcels')

    # Recreate prototype tables matching Revision 1
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
