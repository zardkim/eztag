# eztag 빌드 & 릴리즈 계획서

## 1. 개요

eztag는 GitHub Actions를 통해 릴리즈 태그 push 시 자동으로 Docker 이미지를 빌드하고
Docker Hub에 배포합니다. 최종 사용자(시놀로지 NAS 등)는 소스 빌드 없이
Docker Hub 이미지만으로 설치할 수 있습니다.

---

## 2. 저장소 구조

```
eztag/
├── .github/
│   └── workflows/
│       └── release.yml        ← GitHub Actions 릴리즈 워크플로우
├── backend/
│   ├── Dockerfile
│   └── entrypoint.sh          ← data 디렉토리 자동 생성 포함
├── frontend/
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml         ← Docker Hub 이미지 사용 (배포용)
├── docker-compose.build.yml   ← 로컬 소스 빌드용 오버라이드
├── env.sample                 ← 환경변수 샘플 (git 추적)
└── .env.example               ← 상세 주석 포함 샘플
```

---

## 3. 버전 관리 전략

### Semantic Versioning

```
v{MAJOR}.{MINOR}.{PATCH}
예) v0.3.0, v0.4.0, v1.0.0
```

| 타입 | 예시 | 설명 |
|------|------|------|
| PATCH | v0.3.1 | 버그 수정, 소규모 개선 |
| MINOR | v0.4.0 | 신기능 추가, 하위 호환 유지 |
| MAJOR | v1.0.0 | 대규모 변경, 호환성 변경 |

### 버전 파일 위치

- `backend/app/version.py` → `APP_VERSION`
- `frontend/vite.config.js` → `__APP_VERSION__` (빌드 시 주입)

---

## 4. 릴리즈 절차

### 4-1. 개발 완료 후 버전 업데이트

```bash
# 1. backend/app/version.py 수정
APP_VERSION = "0.4.0"
BUILD_DATE  = "2026-03-19"

# 2. CHANGELOG.md 업데이트
# 3. 변경 사항 commit
git add -A
git commit -m "chore: release v0.4.0"
git push origin main
```

### 4-2. 태그 생성 및 push

```bash
git tag v0.4.0
git push origin v0.4.0
```

→ 태그 push 즉시 GitHub Actions가 자동 실행됩니다.

---

## 5. GitHub Actions 워크플로우 (`release.yml`)

### 트리거

```
tags: v*.*.*  (예: v0.4.0, v1.0.0)
```

### 실행 단계

```
1. Checkout 소스 코드
2. 버전 추출 (태그명에서 파싱)
3. QEMU 설정 (멀티 아키텍처 지원)
4. Docker Buildx 설정
5. Docker Hub 로그인
6. Backend 이미지 빌드 & 푸시 (amd64 + arm64)
7. Frontend 이미지 빌드 & 푸시 (amd64 + arm64)
8. GitHub Release 자동 생성
```

### 생성되는 Docker 이미지 태그

```
zardkim/eztag-backend:v0.4.0   ← 버전 태그
zardkim/eztag-backend:latest   ← 최신 태그 (자동 갱신)

zardkim/eztag-frontend:v0.4.0
zardkim/eztag-frontend:latest
```

### 멀티 아키텍처

| 플랫폼 | 용도 |
|--------|------|
| `linux/amd64` | x86 서버, 일반 PC |
| `linux/arm64` | 시놀로지 ARM NAS, Apple Silicon |

---

## 6. GitHub 시크릿 설정

GitHub 저장소 → Settings → Secrets and variables → Actions 에서 등록:

| 시크릿 이름 | 값 | 설명 |
|------------|-----|------|
| `DOCKERHUB_USERNAME` | `zardkim` | Docker Hub 사용자명 |
| `DOCKERHUB_TOKEN` | `dckr_pat_...` | Docker Hub Access Token |

### Docker Hub Access Token 발급

1. https://hub.docker.com → Account Settings → Security
2. New Access Token → 이름 입력 → Read, Write, Delete 권한
3. 생성된 토큰을 `DOCKERHUB_TOKEN` 시크릿에 등록

---

## 7. 설치 방법 (최종 사용자)

### 최초 설치 (Docker Hub 이미지 사용)

```bash
# 1. 필요 파일만 다운로드 (전체 클론 불필요)
curl -O https://raw.githubusercontent.com/zardkim/eztag/main/docker-compose.yml
curl -O https://raw.githubusercontent.com/zardkim/eztag/main/env.sample

# 2. .env 파일 생성 및 수정
cp env.sample .env
vi .env   # SECRET_KEY, MUSIC_PATH 수정 필수

# 3. 데이터 폴더 생성
mkdir -p data/db data/covers data/logs data/backup
chmod -R 777 data/

# 4. 실행 (이미지 자동 pull)
docker compose up -d
```

### 특정 버전 설치

```bash
VERSION=v0.4.0 docker compose up -d
```

### 업데이트

```bash
docker compose pull
docker compose up -d
```

---

## 8. 로컬 개발 / 소스 빌드

```bash
git clone https://github.com/zardkim/eztag.git
cd eztag
cp env.sample .env
# .env 수정

docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build
```

---

## 9. data 디렉토리 구조

| 호스트 경로 | 컨테이너 경로 | 역할 |
|------------|--------------|------|
| `./data/db` | `/var/lib/postgresql/data` | PostgreSQL 데이터 |
| `./data/covers` | `/app/data/covers` | 커버아트 저장소 |
| `./data/logs` | `/app/data/logs` | 애플리케이션 로그 |
| `./data/backup` | `/app/data/backup` | DB 백업 파일 |

- `data/covers`, `data/logs`, `data/backup` → 백엔드 `entrypoint.sh`에서 자동 생성
- `data/db` → PostgreSQL 컨테이너 시작 시 Docker가 자동 생성

---

## 10. 릴리즈 체크리스트

- [ ] `backend/app/version.py` 버전 업데이트
- [ ] `CHANGELOG.md` 변경 이력 작성
- [ ] 기능 테스트 완료
- [ ] `main` 브랜치에 push
- [ ] `git tag vX.Y.Z && git push origin vX.Y.Z`
- [ ] GitHub Actions 실행 확인
- [ ] Docker Hub 이미지 확인
  - `zardkim/eztag-backend:vX.Y.Z`
  - `zardkim/eztag-frontend:vX.Y.Z`
- [ ] GitHub Release 확인
