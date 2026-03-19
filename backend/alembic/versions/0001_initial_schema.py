"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-08

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "artists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(500), nullable=False, unique=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "albums",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("artist_id", sa.Integer(), sa.ForeignKey("artists.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False, index=True),
        sa.Column("album_artist", sa.String(500), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("genre", sa.String(200), nullable=True),
        sa.Column("cover_path", sa.String(1000), nullable=True),
        sa.Column("track_count", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "tracks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("album_id", sa.Integer(), sa.ForeignKey("albums.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False, index=True),
        sa.Column("artist", sa.String(500), nullable=True, index=True),
        sa.Column("album_artist", sa.String(500), nullable=True),
        sa.Column("album_title", sa.String(500), nullable=True),
        sa.Column("track_no", sa.Integer(), nullable=True),
        sa.Column("disc_no", sa.Integer(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("genre", sa.String(200), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("bitrate", sa.Integer(), nullable=True),
        sa.Column("file_path", sa.String(2000), nullable=False, unique=True, index=True),
        sa.Column("file_format", sa.String(10), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("modified_time", sa.Float(), nullable=True),
        sa.Column("lyrics", sa.Text(), nullable=True),
        sa.Column("has_cover", sa.Boolean(), default=False),
        sa.Column("has_lyrics", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    op.create_table(
        "scan_folders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("path", sa.String(2000), nullable=False, unique=True),
        sa.Column("name", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("scan_folders")
    op.drop_table("tracks")
    op.drop_table("albums")
    op.drop_table("artists")
