# 시놀로지 NAS Docker 설치 가이드

## 사전 준비

- DSM 7.x 이상
- **Container Manager** 패키지 설치 (구 Docker 패키지)
- SSH 접근 활성화 (제어판 → 터미널 및 SNMP → SSH 서비스 활성화)

---

## 1. SSH 접속

```bash
ssh your-username@NAS-IP-주소
```

관리자 계정으로 접속합니다.

---

## 2. 소스 클론

Docker 프로젝트를 저장할 폴더를 만들고 저장소를 클론합니다.

```bash
# 예시: /volume1/docker/eztag 에 설치
mkdir -p /volume1/docker/eztag
cd /volume1/docker
git clone https://github.com/zardkim/eztag.git
cd eztag
```

> **git이 없는 경우**: DSM 패키지 센터에서 Git Server 패키지를 설치하거나,
> PC에서 zip으로 다운로드 후 파일 스테이션으로 복사해도 됩니다.

---

## 3. 환경 설정 파일 생성

```bash
cp .env.example .env
vi .env
```

`.env` 파일을 아래와 같이 수정합니다.

```env
# [필수] 랜덤 시크릿 키 생성 후 입력
SECRET_KEY=여기에-랜덤-문자열-입력

# [필수] 실제 음악 폴더 경로로 변경
MUSIC_PATH=/volume1/music

# DB 비밀번호 (원하는 값으로 변경)
DB_PASSWORD=eztag_password

# 포트 (다른 서비스와 충돌 시 변경)
FRONTEND_PORT=5850
BACKEND_PORT=18011

LOG_LEVEL=INFO
```

### SECRET_KEY 생성 방법

```bash
openssl rand -hex 32
```

출력된 문자열을 `SECRET_KEY` 값으로 사용합니다.

---

## 4. 데이터 폴더 권한 설정

```bash
mkdir -p data/db data/covers data/logs data/backup
chmod -R 777 data/
```

> 시놀로지에서는 Docker 컨테이너가 다른 UID로 실행되므로
> `data/` 하위 폴더에 쓰기 권한이 필요합니다.

---

## 5. Docker 이미지 빌드 및 실행

```bash
sudo docker-compose up -d --build
```

> 최초 빌드는 5~15분 소요됩니다 (NAS 성능에 따라 다름).

### 실행 상태 확인

```bash
sudo docker-compose ps
```

아래와 같이 3개 컨테이너가 모두 `Up` 상태여야 합니다.

```
NAME                STATUS
eztag-postgres-1    Up (healthy)
eztag-backend-1     Up
eztag-frontend-1    Up
```

---

## 6. 접속

브라우저에서 `http://NAS-IP:5850` 으로 접속합니다.

최초 접속 시 관리자 계정 설정 화면이 나타납니다.

---

## 7. 초기 설정

1. 관리자 아이디 / 비밀번호 설정
2. **설정 → 일반** 에서 스캔 폴더 등록
3. **설정 → 메타데이터** 에서 Spotify API 키 입력 (선택)

---

## 포트 충돌 시

`.env` 파일에서 포트를 변경합니다.

```env
FRONTEND_PORT=15850
BACKEND_PORT=18012
```

변경 후 재시작:

```bash
sudo docker-compose down
sudo docker-compose up -d
```

---

## 업데이트

```bash
cd /volume1/docker/eztag
git pull
sudo docker-compose down
sudo docker-compose up -d --build
```

---

## 로그 확인

```bash
# 전체 로그
sudo docker-compose logs -f

# 백엔드만
sudo docker-compose logs -f backend

# 프론트엔드만
sudo docker-compose logs -f frontend
```

---

## 완전 초기화 (주의)

데이터가 모두 삭제됩니다.

```bash
sudo docker-compose down -v
rm -rf data/
```

---

## 자주 묻는 질문

### Q. 음악 파일이 보이지 않아요

- `.env`의 `MUSIC_PATH` 경로가 실제 음악 폴더와 일치하는지 확인
- 설정 → 스캔 폴더를 등록 후 스캔 실행

### Q. 커버아트가 저장되지 않아요

```bash
chmod -R 777 data/covers
```

### Q. LRC 검색이 오래 걸려요

파일당 1~3초 소요되며 정상 동작입니다.
한 번에 많은 파일을 처리하면 시간이 걸리므로 폴더 단위로 나눠서 실행하세요.

### Q. `docker-compose` 명령이 없어요

DSM 7.2 이상에서는 `docker compose` (하이픈 없음) 를 사용합니다.

```bash
sudo docker compose up -d --build
```
