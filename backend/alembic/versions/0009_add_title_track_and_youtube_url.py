"""add_title_track_and_youtube_url

Revision ID: 0009
Revises: 0008
Create Date: 2026-03-22

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0009'
down_revision: Union[str, None] = '0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tracks', sa.Column('is_title_track', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('tracks', sa.Column('youtube_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('tracks', 'youtube_url')
    op.drop_column('tracks', 'is_title_track')
