# 🎵 eztag

음악 라이브러리 메타데이터 관리 및 태그 편집 웹 애플리케이션

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.x-brightgreen)](https://vuejs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://www.postgresql.org/)

---

## 주요 기능

- **파일 브라우저**: 음악 폴더 탐색, 오디오 파일 목록 및 태그 조회
- **태그 편집**: 개별 파일 태그 편집, 일괄(배치) 편집
- **메타데이터 자동 검색**: Spotify, Bugs, Melon, Apple Music 연동
- **커버아트 관리**: 커버 자동 추출, 업로드, 폴더 이미지에서 삽입
- **파일 이동**: 대상 폴더 등록 후 음악 파일 이동
- **태그 기반 파일명 변경**: 패턴 문자열로 일괄 파일명 변경
- **HTML 내보내기**: 트랙 목록 + 앨범 소개 HTML 문서 생성
- **LRC 가사 가져오기 (Get LRC)**: Bugs / LRCLIB 소스에서 LRC 가사 파일 자동 저장
- **자동 스캔 스케줄러**: 설정된 주기로 음악 폴더 자동 스캔
- **백업 / 복원**: DB + 커버아트 tar.gz 백업
- **다국어 지원**: 한국어 / English
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

### 2. `docker-compose.yml` 볼륨 경로 수정

```yaml
volumes:
  - /your/music/path:/music   # 음악 폴더 경로로 변경
```

### 3. 실행

```bash
docker-compose up -d
```

- 프론트엔드: `http://localhost:5850`
- 백엔드 API: `http://localhost:18011`

### 4. 초기 설정

브라우저에서 `http://localhost:5850` 접속 → 관리자 계정 생성 → 설정 완료

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

### 환경 변수 (Backend)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `DATABASE_URL` | - | PostgreSQL 연결 문자열 |
| `MUSIC_BASE_PATH` | `/music` | 음악 라이브러리 루트 경로 |
| `COVERS_PATH` | `/app/data/covers` | 커버아트 저장 경로 |
| `SECRET_KEY` | - | JWT 서명 키 (운영 시 반드시 변경) |
| `LOG_DIR` | `/app/data/logs` | 로그 저장 경로 |
| `BACKUP_DIR` | `/app/data/backup` | 백업 저장 경로 |

### 앱 설정 (Settings 페이지)

| 항목 | 설명 |
|------|------|
| Spotify API | Client ID / Secret 입력 |
| 자동 스캔 주기 | 분 단위 (0 = 비활성화) |
| 이동 대상 폴더 | 파일 이동 시 대상 폴더 목록 |
| Get LRC 폴더 | LRC 가사 검색 기본 폴더 |
| 앱 언어 | 한국어 / English |

---

## 지원 포맷

`.mp3` `.flac` `.m4a` `.ogg` `.aac`

---

## 버전

현재 버전: **v0.3.0**

변경 이력은 [CHANGELOG.md](CHANGELOG.md)를 참조하세요.

---

## 라이선스

MIT
