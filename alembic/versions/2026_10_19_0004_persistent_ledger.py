"""Persistent tamper-evident ledger with immutability trigger

Revision ID: 2026_10_19_0004
Revises: 2026_10_19_0003
Create Date: 2026-10-19 15:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '2026_10_19_0004'
down_revision: Union[str, None] = '2026_10_19_0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        return

    # 1. Create ledger_entries table
    op.create_table(
        'ledger_entries',
        sa.Column('entry_index', sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('parcel_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('dag_number', sa.String(length=32), nullable=True),
        sa.Column('mouza', sa.String(length=128), nullable=True),
        sa.Column('officer_id', sa.String(length=64), nullable=True),
        sa.Column('verdict', sa.String(length=32), nullable=True),
        sa.Column('cited_records', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('payload_hash', sa.String(length=64), nullable=False),
        sa.Column('previous_hash', sa.String(length=64), nullable=False),
        sa.Column('entry_hash', sa.String(length=64), nullable=False),
        sa.Column('signature', sa.String(length=128), nullable=False),
    )
    op.create_index('ix_ledger_entries_entry_index', 'ledger_entries', ['entry_index'], unique=True)
    op.create_index('ix_ledger_entries_dag_number', 'ledger_entries', ['dag_number'])

    # 2. Immutability Trigger: prevent UPDATE and DELETE
    op.execute("""
    CREATE OR REPLACE FUNCTION reject_ledger_tampering()
    RETURNS TRIGGER AS $$
    BEGIN
        RAISE EXCEPTION 'Ledger entries are immutable and cannot be updated or deleted.';
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE TRIGGER trg_ledger_entries_immutable
    BEFORE UPDATE OR DELETE ON ledger_entries
    FOR EACH ROW EXECUTE FUNCTION reject_ledger_tampering();
    """)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        return

    op.execute("DROP TRIGGER IF EXISTS trg_ledger_entries_immutable ON ledger_entries;")
    op.execute("DROP FUNCTION IF EXISTS reject_ledger_tampering();")
    op.drop_table('ledger_entries')
