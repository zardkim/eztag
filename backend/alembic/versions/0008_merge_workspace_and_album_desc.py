"""merge_workspace_and_album_desc

Revision ID: 0008
Revises: 0007, 7df181314453
Create Date: 2026-03-20 10:41:14.964736

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0008'
down_revision: Union[str, None] = ('0007', '7df181314453')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
