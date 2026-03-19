"""Add metadata provider config keys

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-08
"""
from alembic import op

revision: str = "0004"
down_revision: str = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO app_config (key, value, description)
        VALUES
          ('spotify_client_id',     '',      'Spotify API Client ID'),
          ('spotify_client_secret', '',      'Spotify API Client Secret'),
          ('spotify_enabled',       'true',  'Spotify 메타데이터 검색 활성화'),
          ('apple_music_enabled',   'false', 'Apple Music 메타데이터 검색 활성화'),
          ('melon_enabled',         'false', 'Melon 메타데이터 검색 활성화'),
          ('bugs_enabled',          'false', 'Bugs 메타데이터 검색 활성화')
        ON CONFLICT (key) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM app_config
        WHERE key IN (
          'spotify_client_id', 'spotify_client_secret', 'spotify_enabled',
          'apple_music_enabled', 'melon_enabled', 'bugs_enabled'
        )
    """)
