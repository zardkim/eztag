<div align="center">
  <img src="https://raw.githubusercontent.com/zardkim/eztag/main/frontend/public/logo.svg" alt="eztag logo" width="280" />

  <br/>

  [![Version](https://img.shields.io/badge/version-0.5.2-orange)](https://github.com/zardkim/eztag/releases)
  [![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com/)
  [![Vue.js](https://img.shields.io/badge/Vue.js-3.x-brightgreen)](https://vuejs.org/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

  <br/>

  [🇰🇷 한국어](README.md) | 🇺🇸 English
</div>

---

A web application for managing music library metadata and editing audio tags.

## Features

- **File Browser** — Browse music folders, view audio file list and tags
- **Tag Editor** — Individual and batch tag editing, including Description (Comment)
- **Auto Metadata Search** — Spotify, Bugs, Melon, Apple Music integration
- **Cover Art Management** — Auto extract, upload, Google Image search
- **File Mover** — Register destination folders and move music files
- **Rename by Tags** — Batch file rename using pattern strings
- **HTML Export** — Generate HTML with track list, title tracks, and YouTube MV embeds
- **Title Track / YouTube MV** — Mark title tracks and link YouTube URLs (auto search via YouTube Data API v3)
- **Get LRC Lyrics** — Auto-download LRC lyric files from Bugs / LRCLIB
- **Auto Scan Scheduler** — Automatically scan music folders on a set interval
- **Backup / Restore** — DB + cover art tar.gz backup
- **PWA Support** — Install on mobile home screen, offline static asset cache
- **Mobile Optimized** — Responsive layout, home screen (recent folders), bottom tab navigation
- **Multilingual** — Korean / English (switch directly from login screen)
- **Dark Mode** support

## Supported Formats

`.mp3` `.flac` `.m4a` `.ogg` `.aac`

## Architecture

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, Vite, Pinia, Vue Router, vue-i18n, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy, Alembic, APScheduler, Mutagen |
| Database | PostgreSQL 15 |
| Deploy | Docker Compose |

## Docker Compose Installation

### 1. Download the required files

Create a folder and download the two configuration files:

```bash
mkdir eztag && cd eztag

# docker-compose.yml
curl -O https://raw.githubusercontent.com/zardkim/eztag/main/docker-compose.yml

# Environment variable sample
curl -O https://raw.githubusercontent.com/zardkim/eztag/main/env.sample
```

### 2. docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: eztag
      POSTGRES_USER: eztag
      POSTGRES_PASSWORD: ${DB_PASSWORD:-eztag_password}
    volumes:
      - ./data/db:/var/lib/postgresql/data
    networks:
      - eztag-net

  backend:
    image: zardkim/eztag-backend:${VERSION:-latest}
    restart: unless-stopped
    ports:
      - "0.0.0.0:${BACKEND_PORT:-18011}:18011"
    environment:
      DATABASE_URL: postgresql://eztag:${DB_PASSWORD:-eztag_password}@postgres:5432/eztag
      MUSIC_BASE_PATH: /music
      SECRET_KEY: ${SECRET_KEY:?SECRET_KEY must be set in .env file}
    volumes:
      - ${MUSIC_PATH:-./data/library}:/music:ro
      - ./data/covers:/app/data/covers
      - ./data/backup:/app/data/backup
    depends_on:
      - postgres
    networks:
      - eztag-net

  frontend:
    image: zardkim/eztag-frontend:${VERSION:-latest}
    restart: unless-stopped
    ports:
      - "0.0.0.0:${FRONTEND_PORT:-5850}:80"
    depends_on:
      - backend
    networks:
      - eztag-net

networks:
  eztag-net:
    driver: bridge
```

### 3. Configure environment variables

```bash
cp env.sample .env
```

Edit `.env` and set the required values:

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | **(required)** | JWT signing key — generate with `openssl rand -hex 32` |
| `MUSIC_PATH` | `./data/library` | Path to your music folder (Synology: `/volume1/music`, etc.) |
| `DB_PASSWORD` | `eztag_password` | PostgreSQL password |
| `FRONTEND_PORT` | `5850` | Web UI port |
| `BACKEND_PORT` | `18011` | Backend API port |
| `VERSION` | `latest` | Docker image tag |

`.env` example:

```env
SECRET_KEY=your-random-secret-key-32chars
MUSIC_PATH=/volume1/music
DB_PASSWORD=mypassword
FRONTEND_PORT=5850
BACKEND_PORT=18011
VERSION=latest
```

### 4. Start

```bash
docker compose up -d
```

Open `http://localhost:5850` in your browser → create an admin account → start using eztag.

### 5. Update

```bash
docker compose pull && docker compose up -d
```

## Synology NAS Installation

1. Download `docker-compose.yml` and `env.sample` to your PC
2. Copy `env.sample` to `.env` and set `MUSIC_PATH=/volume1/music` (your actual path)
3. Container Manager → Project → Upload `docker-compose.yml` and `.env`, then start

## Settings

| Item | Description |
|------|-------------|
| Spotify API | Enter Client ID / Client Secret |
| YouTube Data API v3 | API key for auto MV search |
| Google CSE | Google Custom Search Engine for cover art |
| Auto Scan Interval | In minutes (0 = disabled) |
| Destination Folders | Target folders for file move |
| Get LRC Folder | Default folder for LRC lyrics search |

## Version History

| Version | Date | Changes |
|---------|------|---------|
| **v0.5.2** | 2026-03-23 | PWA support (mobile home screen, service worker cache), Comment field editing, save speed improvements |
| v0.5.0 | 2026-03-22 | Title track / YouTube MV, mobile layout overhaul, login language toggle |
| v0.4.0 | — | Workspace-based tag editing, file mover, mobile toolbar |
| v0.3.0 | — | LRC lyrics, HTML export, auto scan scheduler |

---

## License

MIT
