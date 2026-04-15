# Changelog

## [0.8.25] - 2026-04-15

### 수정
- 모바일에서 폴더 선택 시 직접 오디오 파일이 없고 오디오가 있는 하위 폴더만 있는 경우, 파일 목록 대신 폴더 그리드만 표시되던 버그 수정
  - `loadFiles()` 완료 후 직접 파일이 0개이고 `has_audio` 하위 폴더가 있으면 자동으로 재귀 로드로 전환
- `loadRecursiveFiles()` 내 `isRecursiveMode` 미완료 스캔 재시도 폴링이 동작하지 않던 버그 수정 (`false` → `true`)

## [0.4.0] - 2026-03-19

### 추가
- 모바일 최적화: Browser, Settings, MiniPlayer, RenameByTagsModal 반응형 레이아웃
- 파일명 변경 패턴 히스토리: 최근 사용 패턴 콤보박스로 선택 (localStorage, 최대 15개)
- HTML 내보내기: 앨범/폴더 단위 독립형 HTML 앨범 쇼케이스 페이지 생성
- 활동 로그 페이지: 태그 저장·파일명 변경·LRC 검색·로그인 등 시스템 전반 로그 확인 (Settings > 활동 로그)
- 라이브러리 LRC 검색: 이동할 폴더의 정리된 파일에 LRC 일괄 검색 (Settings > 라이브러리 LRC)

### 변경
- Settings 탭 네비게이션: 모바일 상단 가로 스크롤, 데스크톱 좌측 세로 탭
- Browser 파일 목록: 모바일 카드뷰 / 데스크톱 테이블 이중 레이아웃

## [0.3.0] - 2026-03-08

### 추가
- 자동 스캔 스케줄러 (APScheduler): `scan_interval_minutes` 설정 연동, 설정 변경 시 즉시 반영
- Spotify 메타데이터 검색: Client Credentials 인증, 트랙/앨범 검색, 커버 URL 다운로드 후 자동 저장
- 메타데이터 일괄 적용: 앨범 단위 Spotify 트랙 목록 조회 → track_no 매칭으로 로컬 트랙에 적용
- 메타데이터 소스 스텁: Apple Music, Melon, Bugs (추후 스크립트 연동 예정)
- 설정 페이지: Spotify API 키 입력, 스케줄러 상태 표시, 즉시 스캔 버튼
- 앨범 상세 페이지: 🔍 메타데이터 검색 버튼 → MetadataSearchModal
- Alembic 마이그레이션 0004 (metadata provider config keys)

## [0.2.0] - 2026-03-08

### 추가
- 설정 페이지 (Settings): 스캔 주기, 커버아트 추출, 지원 포맷, 언어 설정
- DB 기반 설정 저장 (`app_config` 테이블)
- 스캔 이력 로그 DB 저장 (`scan_log` 테이블)
- 파일 로그: `app.log`, `error.log` (RotatingFileHandler, 10MB × 5)
- 백업/복원: `pg_dump` 기반 tar.gz 아카이브 (DB + 커버아트)
- 버전 관리: `version.py` 단일 파일, `/api/health` 버전 응답
- Alembic 마이그레이션 0002 (app_config), 0003 (scan_log)

## [0.1.0] - 2026-03-08

### 추가
- 초기 릴리즈
- 앨범 / 아티스트 / 트랙 라이브러리 관리
- 음악 폴더 스캔 (MP3, FLAC, M4A, OGG)
- 커버아트 자동 추출 및 업로드
- 트랙 태그 편집 (개별 / 일괄)
