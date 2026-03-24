<div align="center">
  <img src="https://raw.githubusercontent.com/zardkim/eztag/main/frontend/public/logo.svg" alt="eztag logo" width="280" />

  <br/>

  [![Version](https://img.shields.io/badge/version-0.8.2-orange)](https://github.com/zardkim/eztag/releases)
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

- **File Browser** — Browse music folders across two separate areas: Workspace and Library
- **Tag Editor** — Individual and batch tag editing, including Description (Comment)
- **Auto Metadata Search** — Spotify, Bugs, Melon, Apple Music integration
- **Cover Art Management** — Auto extract and embed covers (case-insensitive: cover/COVER/Cover), upload
- **Rename by Tags** — Batch file rename using pattern strings
- **HTML Export** — Generate HTML with track list, title tracks, and YouTube MV embeds
- **Title Track / YouTube MV** — Mark title tracks and link YouTube URLs (auto search via YouTube Data API v3), in-app player
- **Get LRC Lyrics** — Auto-download LRC lyric files from Bugs / LRCLIB
- **Backup / Restore** — Full DB backup (settings, presets, metadata) as tar.gz
- **PWA Support** — Install on mobile home screen, offline static asset cache
- **Mobile Optimized** — Responsive layout, home screen (recent folders + clear list), bottom tab navigation
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
curl -O https://raw.githubusercontent.com/zardkim/eztag/main/.env.example
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
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U eztag"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - eztag-net

  backend:
    image: zardkim/eztag-backend:${VERSION:-latest}
    restart: unless-stopped
    ports:
      - "18011:18011"
    environment:
      DATABASE_URL: postgresql://eztag:${DB_PASSWORD:-eztag_password}@postgres:5432/eztag
      MUSIC_BASE_PATH: /music
      WORKSPACE_PATH: /workspace
      SECRET_KEY: ${SECRET_KEY:?SECRET_KEY must be set in .env file}
    volumes:
      - ./data/library:/music
      - ./data/workspace:/workspace
      - ./data/covers:/app/data/covers
      - ./data/logs:/app/data/logs
      - ./data/backup:/app/data/backup
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - eztag-net

  frontend:
    image: zardkim/eztag-frontend:${VERSION:-latest}
    restart: unless-stopped
    ports:
      - "5850:5850"
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
cp .env.example .env
```

Edit `.env` and set the required values:

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | **(required)** | JWT signing key — generate with `openssl rand -hex 32` |
| `DB_PASSWORD` | `eztag_password` | PostgreSQL password |
| `LOG_LEVEL` | `INFO` | Log level (DEBUG / INFO / WARNING / ERROR) |
| `VERSION` | `latest` | Docker image tag |

`.env` example:

```env
SECRET_KEY=your-random-secret-key-32chars
DB_PASSWORD=mypassword
LOG_LEVEL=INFO
VERSION=latest
```

### 4. Connect your music folders

Mount your actual music folders under the library (`./data/library`) and workspace (`./data/workspace`) directories.

**Add Docker volumes** (append to the `volumes` section in `docker-compose.yml`):
```yaml
volumes:
  - ./data/library:/music
  - ./data/workspace:/workspace
  - /path/to/your/music:/music/MyAlbums     # add library folder
  - /path/to/your/work:/workspace/MyWork    # add workspace folder
```

**Symlinks** (from outside the container):
```bash
ln -s /path/to/your/music ./data/library/MyAlbums
ln -s /path/to/your/work  ./data/workspace/MyWork
```

### 5. Start

```bash
docker-compose up -d
```

Open `http://localhost:5850` in your browser → create an admin account → start using eztag.

### 6. Update

```bash
docker-compose pull && docker-compose up -d
```

## Synology NAS Installation

1. Download `docker-compose.yml` and `.env.example` to your PC
2. Rename `.env.example` to `.env` and set the required values (`SECRET_KEY` is mandatory)
3. Container Manager → Project → Upload `docker-compose.yml` and `.env`, then start
4. Add your music folders via additional volume mounts in Container Manager

## Settings

| Item | Description |
|------|-------------|
| Spotify API | Enter Client ID / Client Secret |
| YouTube Data API v3 | API key for auto MV search |
| Get LRC Folder | Default folder for LRC lyrics search |

## Version History

| Version | Date | Changes |
|---------|------|---------|
| **v0.8.0** | 2026-03-24 | Workspace/Library dual areas, YouTube in-app player, auto cover embed, backup stability, various bug fixes |
| v0.7.0 | 2026-03-23 | PWA support, AI cover art generation, security improvements |
| v0.6.0 | 2026-03-23 | YouTube MV panel, folder rename, full i18n expansion, UI improvements |
| v0.5.0 | 2026-03-22 | Title track / YouTube MV, mobile layout overhaul, login language toggle |
| v0.4.0 | — | Workspace-based tag editing, mobile toolbar |
| v0.3.0 | — | LRC lyrics, HTML export |

---

## License

MIT
