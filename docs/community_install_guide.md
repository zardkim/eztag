# eztag v0.8.24 설치 가이드 — 음악 메타데이터 태그 편집기

안녕하세요!

음악 파일의 메타데이터(태그)를 웹 브라우저에서 편리하게 관리할 수 있는 **eztag** 를 소개합니다.  
Docker만 설치되어 있으면 NAS, 홈서버, PC 어디서든 5분 안에 실행할 수 있습니다.

---

## eztag 란?

- MP3, FLAC, M4A, OGG, AAC 파일의 태그를 웹 UI로 편집
- **마법사(Wizard)** 기능으로 자동태그 → 커버아트 → LRC 가사 → 파일명 변경 → 앨범카드 생성을 버튼 하나로 순차 자동 실행
- Spotify / 외부 태그 소스에서 메타데이터 자동 검색 및 적용
- 커버아트 자동 추출·임베드, YouTube MV 연결, HTML 앨범카드 생성
- PWA 지원으로 모바일에서도 앱처럼 사용 가능
- 한국어 / English 다국어 지원, 다크 모드

GitHub: https://github.com/zardkim/eztag

---

## 화면 미리보기

**홈화면 / 파일 목록**

![홈화면](https://raw.githubusercontent.com/zardkim/eztag/main/screenshot/웹화면/홈화면.JPG)

![파일목록](https://raw.githubusercontent.com/zardkim/eztag/main/screenshot/웹화면/파일목록%20페이지.JPG)

**태그 편집 / 자동태그 검색**

![태그편집](https://raw.githubusercontent.com/zardkim/eztag/main/screenshot/웹화면/태그편집%20페이지.JPG)

![자동태그 검색](https://raw.githubusercontent.com/zardkim/eztag/main/screenshot/웹화면/자동태그%20검색.JPG)

**마법사 설정 / HTML 앨범카드**

![마법사 설정](https://raw.githubusercontent.com/zardkim/eztag/main/screenshot/웹화면/설정%20-%20마법사.JPG)

![앨범카드](https://raw.githubusercontent.com/zardkim/eztag/main/screenshot/웹화면/앨범카드.JPG)

**모바일**

![모바일 홈](https://raw.githubusercontent.com/zardkim/eztag/main/screenshot/모바일/홈메뉴.JPG)

---

## 설치 방법 (Docker Compose)

### 준비물

- Docker 및 Docker Compose가 설치된 환경 (NAS, 홈서버, PC 모두 가능)

### 1단계 — 폴더 생성 및 파일 다운로드

터미널(SSH)을 열고 아래 명령어를 실행합니다.

```bash
mkdir eztag && cd eztag

curl -O https://raw.githubusercontent.com/zardkim/eztag/main/docker-compose.yml
curl -O https://raw.githubusercontent.com/zardkim/eztag/main/.env.example
```

### 2단계 — 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 텍스트 편집기로 열어 아래 항목을 수정합니다.

```env
SECRET_KEY=여기에_랜덤_키_입력    # 필수! 아래 명령어로 생성 가능
DB_PASSWORD=원하는_비밀번호
```

> **SECRET_KEY 생성 방법** (터미널에서 실행):
> ```bash
> openssl rand -hex 32
> ```
> 출력된 값을 복사해서 `SECRET_KEY=` 뒤에 붙여넣으면 됩니다.

### 3단계 — 음악 폴더 연결

`docker-compose.yml` 파일의 `backend` 서비스 `volumes` 항목에 내 음악 폴더 경로를 추가합니다.

```yaml
volumes:
  - ./data/library:/music
  - ./data/workspace:/workspace
  - /내/음악/폴더경로:/music/MyMusic      # ← 여기에 실제 경로 추가
  - ./data/covers:/app/data/covers
  - ./data/logs:/app/data/logs
  - ./data/backup:/app/data/backup
```

> 시놀로지 NAS 사용자는 Container Manager에서 볼륨 마운트로 추가해도 됩니다.

### 4단계 — 실행

```bash
docker-compose up -d
```

브라우저에서 `http://서버IP:5850` 접속 → 첫 실행 시 관리자 계정 생성 후 바로 사용할 수 있습니다.

---

## 업데이트 방법

```bash
docker-compose pull && docker-compose up -d
```

---

## 시놀로지 NAS 설치 요약

1. `docker-compose.yml`과 `.env.example`을 PC로 다운로드
2. `.env.example` → `.env`로 이름 변경, `SECRET_KEY` 설정 필수
3. Container Manager → 프로젝트 → `docker-compose.yml`과 `.env` 업로드 후 실행
4. 음악 폴더는 Container Manager에서 추가 볼륨 마운트로 연결

---

## v0.8.24 신기능 — 마법사(Wizard)

이번 버전의 핵심 기능입니다.

파일 목록 상단의 **✦ 마법사** 버튼을 누르면 아래 5단계를 자동으로 순서대로 실행해 줍니다.

| 단계 | 작업 | 지원 소스 |
|:---:|------|----------|
| 1 | 자동 태그 | Spotify, Bugs, Melon, Apple Music |
| 2 | 파일명 변경 | 저장된 패턴 자동 적용 |
| 3 | LRC 가사 검색 | 알송, Bugs, LRCLIB |
| 4 | YouTube MV 검색 | 공식 MV 자동 연결 |
| 5 | 앨범 카드 생성 | HTML 앨범카드 자동 생성 |

- 각 단계 **활성/비활성 토글** 가능 — 필요 없는 단계는 끄면 됩니다
- 특정 단계만 **스킵**해서 나머지만 실행 가능
- 단계 **순서 변경** 후 저장 가능
- **마법사 프리셋** — 자주 쓰는 단계 조합을 저장해두고 원클릭으로 불러오기

앨범 정리 작업을 한 번에 끝낼 수 있어서 매우 편리합니다.

![마법사 설정 화면](https://raw.githubusercontent.com/zardkim/eztag/main/screenshot/웹화면/설정%20-%20마법사.JPG)

---

## 설정 (API 키)

선택 사항이지만 설정하면 자동 검색 기능이 훨씬 강력해집니다.

| 항목 | 설명 |
|------|------|
| Spotify API | Client ID / Client Secret — 자동태그 검색에 사용 |
| YouTube Data API v3 | API 키 — 타이틀곡 MV 자동 검색에 사용 |

설정 방법: eztag 접속 → Settings 메뉴 → 해당 항목에 입력

---

## 지원 포맷

`.mp3` `.flac` `.m4a` `.ogg` `.aac`

---

궁금한 점은 GitHub Issues 또는 댓글로 남겨주세요.  
https://github.com/zardkim/eztag/issues
