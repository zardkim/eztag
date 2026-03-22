# 🎵 eztag

음악 라이브러리 메타데이터 관리 및 태그 편집 웹 애플리케이션

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.x-brightgreen)](https://vuejs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://www.postgresql.org/)
[![Version](https://img.shields.io/badge/version-0.5.0-orange)](https://github.com/zardkim/eztag)

---

## 주요 기능

- **파일 브라우저**: 음악 폴더 탐색, 오디오 파일 목록 및 태그 조회
- **태그 편집**: 개별 파일 태그 편집, 일괄(배치) 편집
- **메타데이터 자동 검색**: Spotify, Bugs, Melon, Apple Music 연동
- **커버아트 관리**: 커버 자동 추출, 업로드, 폴더 이미지에서 삽입
- **파일 이동**: 대상 폴더 등록 후 음악 파일 이동
- **태그 기반 파일명 변경**: 패턴 문자열로 일괄 파일명 변경
- **HTML 내보내기**: 트랙 목록 + 타이틀곡 + YouTube 뮤직비디오 임베드 HTML 생성
- **타이틀곡 / YouTube 뮤직비디오**: 태그 패널에서 타이틀곡 지정 및 YouTube 링크 연결 (YouTube Data API v3 자동 검색)
- **LRC 가사 가져오기 (Get LRC)**: Bugs / LRCLIB 소스에서 LRC 가사 파일 자동 저장
- **자동 스캔 스케줄러**: 설정된 주기로 음악 폴더 자동 스캔
- **백업 / 복원**: DB + 커버아트 tar.gz 백업
- **모바일 최적화**: 반응형 레이아웃, 홈 화면(최근 폴더), 하단 탭 내비게이션
- **다국어 지원**: 한국어 / English (로그인 화면에서 바로 전환 가능)
- **다크 모드** 지원

---

## 스크린샷

> 파일 브라우저, 태그 편집, 자동태그(메타데이터 검색), Get LRC 등 주요 화면

---

## 아키텍처

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│    Backend      │────▶│   PostgreSQL    │
│  Vue 3 + Vite   │     │   FastAPI       │     │      DB         │
│  Nginx :5850    │     │   :18011        │     │   (internal)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

| 레이어 | 기술 |
|--------|------|
| Frontend | Vue 3, Vite, Pinia, Vue Router, vue-i18n, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy, Alembic, APScheduler, Mutagen |
| Database | PostgreSQL 15 |
| 배포 | Docker Compose |

---

## 빠른 시작 (Docker)

### 1. 저장소 클론

```bash
git clone https://github.com/zardkim/eztag.git
cd eztag
```

### 2. 환경 변수 설정

```bash
cp env.sample .env
# .env 파일을 열어 필수 값 수정
```

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `SECRET_KEY` | (필수) | JWT 서명 키 — 랜덤 32자 이상 문자열로 변경 |
| `MUSIC_PATH` | `./data/library` | 음악 폴더 경로 (시놀로지: `/volume1/music` 등) |
| `DB_PASSWORD` | `eztag_password` | PostgreSQL 비밀번호 |
| `FRONTEND_PORT` | `5850` | 프론트엔드 포트 |
| `BACKEND_PORT` | `18011` | 백엔드 API 포트 |

### 3. 실행

```bash
docker compose up -d
```

- 프론트엔드: `http://localhost:5850`
- 백엔드 API: `http://localhost:18011`

### 4. 업데이트

```bash
bash scripts/update.sh
```

### 5. 초기 설정

브라우저에서 `http://localhost:5850` 접속 → 관리자 계정 생성 → 설정 완료

---

## 시놀로지 NAS 설치

1. Container Manager → 프로젝트 → `docker-compose.yml` 업로드
2. `.env` 파일에서 `MUSIC_PATH=/volume1/music` (실제 음악 폴더 경로)로 수정
3. 프로젝트 실행

---

## 개발 환경

### 백엔드

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 18011 --reload
```

### 프론트엔드

```bash
cd frontend
npm install
npm run dev   # 개발 서버 :3000 (API는 :18011로 프록시)
```

---

## 설정

### 앱 설정 (Settings 페이지)

| 항목 | 설명 |
|------|------|
| Spotify API | Client ID / Secret 입력 |
| YouTube Data API v3 | API 키 입력 — 타이틀곡 뮤직비디오 자동 검색 |
| 자동 스캔 주기 | 분 단위 (0 = 비활성화) |
| 이동 대상 폴더 | 파일 이동 시 대상 폴더 목록 |
| Get LRC 폴더 | LRC 가사 검색 기본 폴더 |
| 앱 언어 | 한국어 / English |

---

## 지원 포맷

`.mp3` `.flac` `.m4a` `.ogg` `.aac`

---

## 버전 히스토리

### v0.5.0 (2026-03-22)
- **타이틀곡 / YouTube 뮤직비디오**: 태그 패널에서 타이틀곡 지정 + YouTube API 자동 검색 + 파일 목록 뱃지 표시
- **HTML 내보내기 개선**: 타이틀곡 행 강조, YouTube iframe 임베드
- **모바일 레이아웃 개선**: 홈(최근 폴더) / +(폴더·파일 열기) / 설정 / 아이디 탭 구조로 개편
- **홈 화면**: 최근 작업한 폴더 목록 표시, 빠른 재진입
- **로그인 화면 언어 변경**: 로그인 페이지에서 한국어/English 전환 가능
- **Docker 개선**: `env.sample` 추가, `scripts/update.sh` 업데이트 스크립트, 시놀로지 NAS 지원
- DB 마이그레이션: `tracks` 테이블에 `is_title_track`, `youtube_url` 컬럼 추가

### v0.4.0
- 워크스페이스 기반 태그 편집 워크플로우
- 폴더 이동 기능 (MoveToDestinationModal)
- 모바일 툴바 Teleport 지원

### v0.3.0
- LRC 가사 자동 가져오기 (Bugs / LRCLIB)
- HTML 내보내기 (트랙 목록)
- 자동 스캔 스케줄러

---

## 라이선스

MIT
