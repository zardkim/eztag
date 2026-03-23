<div align="center">
  <img src="https://raw.githubusercontent.com/zardkim/eztag/main/frontend/public/logo.svg" alt="eztag logo" width="280" />

  <br/>

  [![Version](https://img.shields.io/badge/version-0.7.0-orange)](https://github.com/zardkim/eztag/releases)
  [![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com/)
  [![Vue.js](https://img.shields.io/badge/Vue.js-3.x-brightgreen)](https://vuejs.org/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

  <br/>

  🇰🇷 한국어 | [🇺🇸 English](README.en.md)
</div>

---

음악 라이브러리 메타데이터 관리 및 태그 편집 웹 애플리케이션

## 주요 기능

- **파일 브라우저** — 음악 폴더 탐색, 오디오 파일 목록 및 태그 조회
- **태그 편집** — 개별/일괄(배치) 태그 편집, 설명(Comment) 포함
- **메타데이터 자동 검색** — Spotify, Bugs, Melon, Apple Music 연동
- **커버아트 관리** — 커버 자동 추출, 업로드, Google 이미지 검색
- **AI 커버아트 생성** — Google Imagen 4 연동, 분위기·연도·앨범명 기반 자동 생성 (Google AI Studio API 필요)
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

## 지원 포맷

`.mp3` `.flac` `.m4a` `.ogg` `.aac`

## 아키텍처

| 레이어 | 기술 |
|--------|------|
| Frontend | Vue 3, Vite, Pinia, Vue Router, vue-i18n, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy, Alembic, APScheduler, Mutagen |
| Database | PostgreSQL 15 |
| 배포 | Docker Compose |

## Docker Compose 설치

### 1. 설치 파일 다운로드

설치할 폴더를 만들고, 설정 파일 두 개를 다운로드합니다.

```bash
mkdir eztag && cd eztag

# docker-compose.yml
curl -O https://raw.githubusercontent.com/zardkim/eztag/main/docker-compose.yml

# 환경 변수 샘플
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

### 3. 환경 변수 설정

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

`.env` 예시:

```env
SECRET_KEY=your-random-secret-key-32chars
MUSIC_PATH=/volume1/music
DB_PASSWORD=mypassword
FRONTEND_PORT=5850
BACKEND_PORT=18011
VERSION=latest
```

### 4. 실행

```bash
docker compose up -d
```

브라우저에서 `http://localhost:5850` 접속 → 관리자 계정 생성 후 사용

### 5. 업데이트

```bash
docker compose pull && docker compose up -d
```

## 시놀로지 NAS 설치

1. `docker-compose.yml`과 `env.sample`을 PC에 다운로드
2. `env.sample`을 `.env`로 이름 변경 후 필수 값 수정 (`SECRET_KEY` 필수, `MUSIC_PATH` 실제 경로로 변경)
3. Container Manager → 프로젝트 → `docker-compose.yml`과 `.env` 업로드 후 실행

## 설정 (Settings 페이지)

| 항목 | 설명 |
|------|------|
| Spotify API | Client ID / Client Secret 입력 |
| YouTube Data API v3 | API 키 입력 — 타이틀곡 MV 자동 검색 |
| 자동 스캔 주기 | 분 단위 (0 = 비활성화) |
| 이동 대상 폴더 | 파일 이동 시 대상 폴더 목록 |
| Get LRC 폴더 | LRC 가사 검색 기본 폴더 |

## 버전 히스토리

| 버전 | 날짜 | 주요 변경사항 |
|------|------|--------------|
| **v0.7.0** | 2026-03-23 | AI 커버아트 생성 (Google Imagen 4) — 분위기·연도·키워드 기반 |
| v0.6.0 | 2026-03-23 | YouTube MV 패널, 폴더 이름 변경, i18n 전면 확장, UI 전반 개선 |
| v0.5.0 | 2026-03-22 | 타이틀곡/YouTube MV, 모바일 레이아웃 개편, 로그인 언어 전환 |
| v0.4.0 | — | 워크스페이스 기반 태그 편집, 파일 이동, 모바일 툴바 |
| v0.3.0 | — | LRC 가사 자동 가져오기, HTML 내보내기, 자동 스캔 스케줄러 |

---

## License

MIT
