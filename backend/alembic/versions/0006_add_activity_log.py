"""Add activity_log table

Revision ID: 0006
Revises: 30c6cc7f8f59
Create Date: 2026-03-19
"""
from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: str = "30c6cc7f8f59"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "activity_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("log_type", sa.String(30), nullable=False),
        sa.Column("action", sa.String(100), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("username", sa.String(100), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_activity_log_created_at", "activity_log", ["created_at"])
    op.create_index("ix_activity_log_log_type", "activity_log", ["log_type"])


def downgrade() -> None:
    op.drop_index("ix_activity_log_log_type", "activity_log")
    op.drop_index("ix_activity_log_created_at", "activity_log")
    op.drop_table("activity_log")
