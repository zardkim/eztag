"""Add app_config table

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-08
"""
from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: str = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.execute("""
        INSERT INTO app_config (key, value, description) VALUES
        ('scan_interval_minutes', '0', '자동 스캔 주기 (분). 0=비활성화'),
        ('extract_covers', 'true', '커버아트 자동 추출 여부'),
        ('supported_formats', '.mp3,.flac,.m4a,.ogg,.aac', '지원 파일 포맷 (콤마 구분)'),
        ('app_language', 'ko', '앱 언어 (ko/en)'),
        ('cover_size', '500', '커버 이미지 최대 크기 (px)'),
        ('cleanup_on_scan', 'false', '스캔 시 누락 파일 자동 정리')
    """)


def downgrade() -> None:
    op.drop_table("app_config")
