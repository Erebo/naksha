"""Add union_land_officer to officers role check constraint

Revision ID: 2026_10_19_0003
Revises: 2026_10_19_0002
Create Date: 2026-10-19 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '2026_10_19_0003'
down_revision: Union[str, None] = '2026_10_19_0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        return

    op.drop_constraint('chk_officers_role', 'officers', type_='check')
    op.create_check_constraint(
        'chk_officers_role',
        'officers',
        "role IN ('ac_land', 'kanungo', 'surveyor', 'sub_registrar', 'dc', 'admin', 'auditor', 'union_land_officer')"
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        return

    op.drop_constraint('chk_officers_role', 'officers', type_='check')
    op.create_check_constraint(
        'chk_officers_role',
        'officers',
        "role IN ('ac_land', 'kanungo', 'surveyor', 'sub_registrar', 'dc', 'admin', 'auditor')"
    )
