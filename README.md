<div align="center">
  <img src="https://raw.githubusercontent.com/zardkim/eztag/main/frontend/public/logo.svg" alt="eztag logo" width="280" />

  <br/>

  [![Version](https://img.shields.io/badge/version-0.8.17-orange)](https://github.com/zardkim/eztag/releases)
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

- **파일 브라우저** — 작업공간/라이브러리 두 영역으로 음악 폴더 탐색, 오디오 파일 목록 및 태그 조회
- **태그 편집** — 개별/일괄(배치) 태그 편집, 설명(Comment) 포함
- **메타데이터 자동 검색** — Spotify 및 외부 태그 지원
- **커버아트 관리** — 커버 자동 추출·임베드 (대소문자 무관 cover/COVER/Cover 파일 자동 인식), 업로드
- **태그 기반 파일명 변경** — 패턴 문자열로 일괄 파일명 변경
- **HTML 앨범카드** — 트랙 목록 + 타이틀곡 + YouTube MV 임베드 HTML 생성 (소개글 10줄 이상 시 접기/펼치기)
- **타이틀곡 / YouTube MV** — 타이틀곡 지정 및 YouTube 링크 연결 (공식 MV 자동 검색), 인앱 플레이어 재생
- **LRC 가사 가져오기** — 외부 태그 지원 소스에서 LRC 가사 파일 자동 저장
- **백그라운드 작업** — LRC 검색 / YouTube 검색을 백그라운드로 실행, 다른 페이지 이동 후에도 계속 진행
- **백업 / 복원** — DB 전체(설정·프리셋 포함) tar.gz 백업
- **PWA 지원** — 모바일 홈 화면에 앱 추가, 오프라인 정적 자산 캐시
- **모바일 최적화** — 반응형 레이아웃, 홈(최근 폴더 + 목록 지우기), 하단 탭 내비게이션
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
      - "5850:80"
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
cp .env.example .env
```

`.env` 파일을 열어 필수 값을 수정합니다:

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `SECRET_KEY` | **(필수)** | JWT 서명 키 — `openssl rand -hex 32` 로 생성 |
| `DB_PASSWORD` | `eztag_password` | PostgreSQL 비밀번호 |
| `LOG_LEVEL` | `INFO` | 로그 레벨 (DEBUG / INFO / WARNING / ERROR) |
| `VERSION` | `latest` | Docker 이미지 태그 |

`.env` 예시:

```env
SECRET_KEY=your-random-secret-key-32chars
DB_PASSWORD=mypassword
LOG_LEVEL=INFO
VERSION=latest
```

### 4. 음악 폴더 연결

라이브러리(`./data/library`)와 작업공간(`./data/workspace`) 아래에 실제 음악 폴더를 연결합니다.

**Docker 볼륨 추가** (`docker-compose.yml` volumes 섹션에 추가):
```yaml
volumes:
  - ./data/library:/music
  - ./data/workspace:/workspace
  - /path/to/your/music:/music/MyAlbums     # 라이브러리 폴더 추가
  - /path/to/your/work:/workspace/MyWork    # 작업공간 폴더 추가
```

**심볼릭 링크** (컨테이너 외부에서):
```bash
ln -s /path/to/your/music ./data/library/MyAlbums
ln -s /path/to/your/work  ./data/workspace/MyWork
```

### 5. 실행

```bash
docker-compose up -d
```

브라우저에서 `http://localhost:5850` 접속 → 관리자 계정 생성 후 사용

### 6. 업데이트

```bash
docker-compose pull && docker-compose up -d
```

## 시놀로지 NAS 설치

1. `docker-compose.yml`과 `.env.example`을 PC에 다운로드
2. `.env.example`을 `.env`로 이름 변경 후 필수 값 수정 (`SECRET_KEY` 필수)
3. Container Manager → 프로젝트 → `docker-compose.yml`과 `.env` 업로드 후 실행
4. 음악 폴더는 Container Manager에서 추가 볼륨 마운트로 연결

## 설정 (Settings 페이지)

| 항목 | 설명 |
|------|------|
| Spotify API | Client ID / Client Secret 입력 |
| YouTube Data API v3 | API 키 입력 — 타이틀곡 MV 자동 검색 |
| LRC 검색 기본설정 | 기본 LRC 소스 선택 (외부 태그 지원), 카드형 UI로 선택 |
| Get LRC 폴더 | LRC 가사 검색 기본 폴더 |

## 버전 히스토리

| 버전 | 날짜 | 주요 변경사항 |
|------|------|--------------|
| **v0.8.17** | 2026-03-30 | 외부 태그 지원 LRC 검색 추가, 앨범카드 소개 접기/펼치기, 설정 LRC 카드형 UI, YouTube MV 검색 정확도 강화, 미니플레이어 비트레이트 1줄 표시 |
| v0.8.16 | 2026-03-29 | 자동태그 검색모드 확장, 앨범설명 저장 수정, 앨범아트 캐시, 파일목록 단일렌더, HTML뷰어 모바일 닫기버튼, 앨범카드 파일명 형식 변경 |
| v0.8.15 | 2026-03-29 | 앨범설명 HTML카드 반영, 모바일 하단메뉴 개편, 폴더피커 마지막경로 기억 |
| v0.8.14 | 2026-03-29 | 백그라운드 LRC/YouTube 검색, 폴더 CRUD, 재귀 폴더 열기 등 다수 개선 |
| v0.8.13 | 2026-03-28 | 앨범카드 리네임, YouTube 다이얼로그 개선, Hero 그라데이션 강화 |
| v0.8.12 | 2026-03-28 | 외부 태그 지원 안정화, LRC 검색 안정화 |
| v0.8.10 | 2026-03-27 | 앨범카드 HTML 내보내기 개선, 장르·레이블 표시 |
| v0.8.4  | 2026-03-24 | HTML 뷰어 사이드바 클릭 버그 수정, YouTube 검색 정확도 개선 |
| v0.8.0  | 2026-03-24 | 작업공간/라이브러리 이중 영역, YT 인앱 플레이어, 커버 자동 임베드, 백업 안정화 |
| v0.7.0  | 2026-03-23 | PWA 지원, AI 커버아트 생성, 보안 개선 |
| v0.6.0  | 2026-03-23 | YouTube MV 패널, 폴더 이름 변경, i18n 전면 확장, UI 전반 개선 |
| v0.5.0  | 2026-03-22 | 타이틀곡/YouTube MV, 모바일 레이아웃 개편, 로그인 언어 전환 |
| v0.4.0  | — | 워크스페이스 기반 태그 편집, 모바일 툴바 |
| v0.3.0  | — | LRC 가사 자동 가져오기, HTML 내보내기 |

---

## License

MIT
