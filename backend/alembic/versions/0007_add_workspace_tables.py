"""Add workspace tables

Revision ID: 0007
Revises: 0006
Create Date: 2026-03-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0007"
down_revision: str = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # workspace_sessions
    op.create_table(
        "workspace_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="editing"),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("username", sa.String(100), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_workspace_sessions_status", "workspace_sessions", ["status"])

    # workspace_items
    op.create_table(
        "workspace_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("workspace_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("original_tags", JSONB(), nullable=True),
        sa.Column("pending_tags", JSONB(), nullable=True),
        sa.Column("pending_rename", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("apply_error", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_workspace_items_session_id", "workspace_items", ["session_id"])
    op.create_index("ix_workspace_items_file_path", "workspace_items", ["file_path"])

    # workspace_history_ops
    op.create_table(
        "workspace_history_ops",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("workspace_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("op_type", sa.String(30), nullable=False),
        sa.Column("op_detail", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_workspace_history_ops_session_id", "workspace_history_ops", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_workspace_history_ops_session_id", "workspace_history_ops")
    op.drop_table("workspace_history_ops")
    op.drop_index("ix_workspace_items_file_path", "workspace_items")
    op.drop_index("ix_workspace_items_session_id", "workspace_items")
    op.drop_table("workspace_items")
    op.drop_index("ix_workspace_sessions_status", "workspace_sessions")
    op.drop_table("workspace_sessions")
