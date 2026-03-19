"""Add scan_log table

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-08
"""
from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: str = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scan_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scan_type", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("folder_path", sa.String(2000), nullable=True),
        sa.Column("scanned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("added", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration", sa.Float(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_scan_log_started_at", "scan_log", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_scan_log_started_at", "scan_log")
    op.drop_table("scan_log")
