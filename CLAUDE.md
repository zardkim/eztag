# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**eztag** is a music library management and tag editing application. It provides folder scanning, metadata enrichment via Spotify, cover art management, batch tag editing, and automated scheduling.

## Development Commands

### Frontend (Vue 3 + Vite)
```bash
cd frontend
npm install
npm run dev      # Dev server on port 3000 (proxies /api to localhost:18011)
npm run build    # Production build
```

### Backend (FastAPI + PostgreSQL)
```bash
cd backend
python3 -m venv .venv       # 최초 1회
source .venv/bin/activate   # 터미널마다 실행
pip install -r requirements.txt
alembic upgrade head   # Run DB migrations
uvicorn app.main:app --host 0.0.0.0 --port 18011 --reload
```

### Database Migrations
```bash
cd backend
# 마이그레이션 생성: --rev-id로 순번 명시 필수
alembic revision --autogenerate --rev-id 0007 -m "add_feature_name"
alembic upgrade head   # 적용
```

**Alembic 파일명 규칙:** `NNNN_description.py` 형식 (4자리 순번)
- 예: `0007_add_library_lrc.py`, `0008_add_user_prefs.py`
- `alembic revision` 시 항상 `--rev-id NNNN` 옵션으로 순번 지정

### 버전 관리
```bash
# 릴리즈 (버전 올리기)
./scripts/release.sh 0.5.0   # 버전 지정
./scripts/release.sh          # VERSION 파일 현재 값 사용

# 로컬 Docker 빌드
./scripts/build-local.sh        # 빌드만
./scripts/build-local.sh --push # 빌드 + Docker Hub 푸시

# GitHub Actions 자동 빌드 (권장)
git tag v0.5.0 && git push origin main --tags
```

**버전 단일 소스:** 프로젝트 루트 `VERSION` 파일
- `release.sh` 실행 시 `backend/app/version.py`, `frontend/package.json` 자동 동기화
- **절대 `version.py`나 `package.json`을 직접 수정하지 말 것**

**Semantic Versioning 기준:**
- `PATCH` (x.x.+1): 버그 수정, UI 개선, 소규모 수정
- `MINOR` (x.+1.0): 신기능 추가
- `MAJOR` (+1.0.0): 하위 호환 불가 DB 스키마 변경, 대규모 구조 변경

### Docker (Production)
```bash
docker-compose up -d   # Starts postgres (internal), backend (:18011), frontend (:5850)
```

## Architecture

### 3-Tier Structure
- **Frontend**: Vue 3 SPA → Nginx (port 5850), built with Vite, state via Pinia
- **Backend**: FastAPI (port 18011) with SQLAlchemy ORM, APScheduler background jobs
- **Database**: PostgreSQL 15 with Alembic migrations

### Backend Layout (`backend/app/`)
- `main.py` — FastAPI app setup, lifespan context, router registration, static file serving
- `api/` — FastAPI routers: `albums`, `artists`, `tracks`, `scan`, `covers`, `config`, `metadata`, `logs`, `backup`, `scheduler_api`
- `models/` — SQLAlchemy ORM models: `Artist`, `Album`, `Track`, `ScanFolder`, `AppConfig`, `ScanLog`
- `schemas/` — Pydantic request/response schemas
- `core/` — Business logic:
  - `scanner.py` — `MusicScanner` class for recursive folder scanning and track diffing
  - `tag_reader.py` / `tag_writer.py` — Mutagen-based tag I/O for MP3 (ID3), FLAC (Vorbis), M4A (iTunes atoms), OGG
  - `cover_extractor.py` — Extract embedded covers + find local folder images; stores with MD5-hash paths
  - `config_store.py` — Key-value config from `app_config` table with defaults
  - `scheduler.py` — APScheduler job manager (timezone: Asia/Seoul)
  - `backup_manager.py` — `pg_dump` + `tar.gz` backup/restore
  - `metadata/spotify.py` — Spotify Client Credentials flow for track/album search and metadata fetch
  - `metadata/apple_music.py`, `melon.py`, `bugs.py` — Stubs ready for implementation

### Frontend Layout (`frontend/src/`)
- `router/index.js` — Vue Router: Albums, Artists, Tracks, Scan, Settings
- `views/` — Page components (Albums, AlbumDetail, Artists, Tracks, Scan, Settings)
- `components/` — MetadataSearchModal, TrackEditModal, BatchEditModal, ConfigRow
- `stores/` — Pinia stores: `library.js` (albums/artists), `theme.js` (dark/light)
- `api/` — Axios modules per domain (index, config, metadata, logs, backup)
- `i18n/` — Vue-i18n with `ko.js` (default) and `en.js` translations

### Key Data Flow
1. **Scan**: `POST /api/scan/start` → `MusicScanner.scan()` → reads tags via mutagen → upserts Artists/Albums/Tracks in DB → extracts/stores cover art
2. **Metadata Enrichment**: Frontend search modal → `GET /api/metadata/search` → Spotify API → `POST /api/metadata/apply/{id}` → writes tags to file + updates DB
3. **Config**: All settings persisted in `app_config` table (key-value); loaded via `config_store.get_all_config()`
4. **Scheduling**: On startup, scheduler reads `scan_interval_minutes` from config and registers APScheduler job; reschedules when config changes

### Database Tables
`artists`, `albums`, `tracks`, `scan_folder`, `app_config` (key-value settings), `scan_log`

### Supported Audio Formats
`.mp3`, `.flac`, `.m4a`, `.ogg`, `.aac`

### Docker Volume Mounts
- `/volume1/music:/music` (read-only) — music library root
- `./data/covers` — extracted/uploaded cover art (MD5 hash path structure)
- `./data/logs` — `app.log` and `error.log`
- `./data/backup` — `eztag_backup_YYYYMMDD_HHMMSS.tar.gz` archives

## Configuration

Backend settings via environment variables (`app/config.py`):
- `DATABASE_URL` — PostgreSQL connection string
- `MUSIC_BASE_PATH` — Base path for music files (default: `/music`)
- `COVERS_PATH` — Cover art storage directory
- `LOG_DIR`, `LOG_LEVEL`

Runtime settings stored in `app_config` DB table (managed via Settings page):
- `spotify_client_id`, `spotify_client_secret`, `spotify_enabled`
- `scan_interval_minutes` (0 = disabled), `extract_covers`, `supported_formats`
- `app_language` (`ko`/`en`), `cover_size`, `cleanup_on_scan`
- `apple_music_enabled`, `melon_enabled`, `bugs_enabled` (stubs)
