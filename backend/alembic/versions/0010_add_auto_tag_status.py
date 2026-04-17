"""add_auto_tag_status

Revision ID: 0010
Revises: 0009
Create Date: 2026-04-16

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0010'
down_revision: Union[str, None] = '0009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tracks', sa.Column('auto_tag_status', sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column('tracks', 'auto_tag_status')
