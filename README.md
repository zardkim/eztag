<div align="center">
  <img src="https://raw.githubusercontent.com/zardkim/eztag/main/frontend/public/logo.svg" alt="eztag logo" width="280" />

  <br/>

  [![Version](https://img.shields.io/badge/version-0.5.2-orange)](https://github.com/zardkim/eztag/releases)
  [![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com/)
  [![Vue.js](https://img.shields.io/badge/Vue.js-3.x-brightgreen)](https://vuejs.org/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

  <br/>

  **[한국어](#-한국어) | [English](#-english)**
</div>

---

## 🇰🇷 한국어

음악 라이브러리 메타데이터 관리 및 태그 편집 웹 애플리케이션

### 주요 기능

- **파일 브라우저** — 음악 폴더 탐색, 오디오 파일 목록 및 태그 조회
- **태그 편집** — 개별/일괄(배치) 태그 편집, 설명(Comment) 포함
- **메타데이터 자동 검색** — Spotify, Bugs, Melon, Apple Music 연동
- **커버아트 관리** — 커버 자동 추출, 업로드, Google 이미지 검색
- **파일 이동** — 대상 폴더 등록 후 음악 파일 이동
- **태그 기반 파일명 변경** — 패턴 문자열로 일괄 파일명 변경
- **HTML 내보내기** — 트랙 목록 + 타이틀곡 + YouTube 뮤직비디오 임베드 HTML 생성
- **타이틀곡 / YouTube MV** — 타이틀곡 지정 및 YouTube 링크 연결 (YouTube Data API v3 자동 검색)
- **LRC 가사 가져오기** — Bugs / LRCLIB 소스에서 LRC 가사 파일 자동 저장
- **자동 스캔 스케줄러** — 설정된 주기로 음악 폴더 자동 스캔
- **백업 / 복원** — DB + 커버아트 tar.gz 백업
- **PWA 지원** — 모바일 홈 화면에 앱 추가, 오프라인 정적 자산 캐시
- **모바일 최적화** — 반응형 레이아웃, 홈(최근 폴더), 하단 탭 내비게이션
- **다국어** — 한국어 / English (로그인 화면에서 바로 전환)
- **다크 모드** 지원

### 지원 포맷

`.mp3` `.flac` `.m4a` `.ogg` `.aac`

### 아키텍처

| 레이어 | 기술 |
|--------|------|
| Frontend | Vue 3, Vite, Pinia, Vue Router, vue-i18n, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy, Alembic, APScheduler, Mutagen |
| Database | PostgreSQL 15 |
| 배포 | Docker Compose |

### Docker Compose 설치

#### 1. 저장소 클론

```bash
git clone https://github.com/zardkim/eztag.git
cd eztag
```

#### 2. 환경 변수 설정

```bash
cp env.sample .env
```

`.env` 파일을 열어 필수 값을 수정합니다:

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `SECRET_KEY` | **(필수)** | JWT 서명 키 — `openssl rand -hex 32` 로 생성 |
| `MUSIC_PATH` | `./data/library` | 음악 폴더 경로 (시놀로지: `/volume1/music` 등) |
| `DB_PASSWORD` | `eztag_password` | PostgreSQL 비밀번호 |
| `FRONTEND_PORT` | `5850` | 웹 UI 접속 포트 |
| `BACKEND_PORT` | `18011` | 백엔드 API 포트 |
| `VERSION` | `latest` | Docker 이미지 태그 |

#### 3. docker-compose.yml 예시

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

#### 4. 실행

```bash
docker compose up -d
```

브라우저에서 `http://localhost:5850` 접속 → 관리자 계정 생성 후 사용

#### 4. 업데이트

```bash
bash scripts/update.sh
```

또는 수동으로:

```bash
docker compose pull
docker compose up -d
```

### 시놀로지 NAS 설치

1. `env.sample`을 `.env`로 복사 후 `MUSIC_PATH=/volume1/music`(실제 경로)으로 수정
2. Container Manager → 프로젝트 → `docker-compose.yml` 업로드
3. `.env` 파일 업로드 후 프로젝트 실행

### 설정 (Settings 페이지)

| 항목 | 설명 |
|------|------|
| Spotify API | Client ID / Client Secret 입력 |
| YouTube Data API v3 | API 키 입력 — 타이틀곡 MV 자동 검색 |
| Google CSE | Google Custom Search Engine — 커버아트 이미지 검색 |
| 자동 스캔 주기 | 분 단위 (0 = 비활성화) |
| 이동 대상 폴더 | 파일 이동 시 대상 폴더 목록 |
| Get LRC 폴더 | LRC 가사 검색 기본 폴더 |

### 버전 히스토리

| 버전 | 날짜 | 주요 변경사항 |
|------|------|--------------|
| **v0.5.2** | 2026-03-23 | PWA 지원 (모바일 홈 화면 추가, 서비스 워커 캐시), 태그 설명(Comment) 편집, 저장 속도 개선 |
| v0.5.1 | 2026-03-23 | 태그 설명(Comment) 편집 저장, 배치 저장 API, 병렬 파일 I/O |
| v0.5.0 | 2026-03-22 | 타이틀곡/YouTube MV, 모바일 레이아웃 개편, 로그인 언어 전환 |
| v0.4.0 | — | 워크스페이스 기반 태그 편집, 파일 이동, 모바일 툴바 |
| v0.3.0 | — | LRC 가사 자동 가져오기, HTML 내보내기, 자동 스캔 스케줄러 |

---

## 🇺🇸 English

A web application for managing music library metadata and editing audio tags.

### Features

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

### Supported Formats

`.mp3` `.flac` `.m4a` `.ogg` `.aac`

### Architecture

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, Vite, Pinia, Vue Router, vue-i18n, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy, Alembic, APScheduler, Mutagen |
| Database | PostgreSQL 15 |
| Deploy | Docker Compose |

### Docker Compose Installation

#### 1. Clone the repository

```bash
git clone https://github.com/zardkim/eztag.git
cd eztag
```

#### 2. Configure environment variables

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

#### 3. docker-compose.yml example

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

#### 4. Start

```bash
docker compose up -d
```

Open `http://localhost:5850` in your browser → create an admin account → start using eztag.

#### 4. Update

```bash
bash scripts/update.sh
```

Or manually:

```bash
docker compose pull
docker compose up -d
```

### Synology NAS Installation

1. Copy `env.sample` to `.env` and set `MUSIC_PATH=/volume1/music` (your actual path)
2. Container Manager → Project → Upload `docker-compose.yml`
3. Upload `.env` and start the project

### Settings

| Item | Description |
|------|-------------|
| Spotify API | Enter Client ID / Client Secret |
| YouTube Data API v3 | API key for auto MV search |
| Google CSE | Google Custom Search Engine for cover art |
| Auto Scan Interval | In minutes (0 = disabled) |
| Destination Folders | Target folders for file move |
| Get LRC Folder | Default folder for LRC lyrics search |

### Version History

| Version | Date | Changes |
|---------|------|---------|
| **v0.5.2** | 2026-03-23 | PWA support (mobile home screen install, service worker cache), Comment field editing, save speed improvements |
| v0.5.1 | 2026-03-23 | Comment tag editing, batch stage API, parallel file I/O |
| v0.5.0 | 2026-03-22 | Title track / YouTube MV, mobile layout overhaul, login language toggle |
| v0.4.0 | — | Workspace-based tag editing, file mover, mobile toolbar |
| v0.3.0 | — | LRC lyrics, HTML export, auto scan scheduler |

---

## License

MIT
