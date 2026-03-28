# Bugs Music 403 Forbidden 해결 계획

> 작성일: 2026-03-29
> 대상: `backend/app/core/metadata/bugs.py`, `bugs_lyrics.py`, 및 메타데이터 수집 전반

---

## 1. 문제 분석

### 현재 구조

| 파일 | 엔드포인트 | 방식 | 403 위험도 |
|------|-----------|------|-----------|
| `bugs.py` | `m.bugs.co.kr/api/getSearchList` | JSON API | 낮음 (공개 API) |
| `bugs.py` | `music.bugs.co.kr/album/{id}` | HTML 스크래핑 | **높음** (봇 차단) |
| `bugs_lyrics.py` | `m.bugs.co.kr/api/getSearchList` | JSON API | 낮음 |
| `bugs_lyrics.py` | `api.bugs.co.kr/3/tracks/{id}/lyrics` | JSON API | 중간 (고정 API 키) |

### 403 발생 원인
- `music.bugs.co.kr/album/{id}` — Cloudflare 또는 자체 봇 탐지로 서버 IP 차단
- 반복 요청 시 Rate Limiting 적용 (테스트 중 차단 경험)
- `requests` 라이브러리의 기본 헤더가 봇으로 탐지됨
- 쿠키/세션 없이 직접 앨범 페이지 접근 시 차단

---

## 2. 권장 4단계 폴백 구조

```
1순위: 로컬 태그 (mutagen)         → 이미 있는 태그 즉시 사용
2순위: 공개 API (lrclib, Bugs API)  → 빠르고 안정적
3순위: requests + 강화 설정        → 재시도/지연/세션 개선
4순위: Playwright (최후 fallback)  → 브라우저 재사용, 리소스 차단
```

---

## 3. 단계별 구현 계획

### 1순위: 로컬 태그 우선 활용
- 이미 `tag_reader.py`가 mutagen으로 읽고 있음
- **추가 작업 없음** — 메타데이터 API는 로컬 태그가 부족할 때만 호출

### 2순위: 공개 API 최대 활용

#### LRC (가사 싱크)
```
현재: lrclib → bugs_lyrics 순서
개선: lrclib 먼저 (성공률 높음, 무제한 API), 실패 시 Bugs 시도
```

#### 메타데이터 (앨범/트랙 정보)
- `m.bugs.co.kr/api/getSearchList` — 현재도 403 없이 작동 중 (유지)
- `api.bugs.co.kr/3/tracks/{id}/lyrics` — 현재도 작동 중 (유지)
- **문제 구간**: `music.bugs.co.kr/album/{id}` HTML 스크래핑 → 3/4순위로 이동

### 3순위: requests 강화 (`bugs.py` `get_album_tracks` 개선)

#### 3-1. Session + 쿠키 유지
```python
# 현재 (매번 새 연결)
resp = requests.get(url, headers=_HEADERS, timeout=15)

# 개선 (세션 재사용 + 홈 방문 → 쿠키 획득 후 앨범 접근)
_session = requests.Session()
_session.headers.update(_HEADERS)

def _warm_session():
    """메인 페이지 방문으로 쿠키 획득."""
    try:
        _session.get("https://music.bugs.co.kr/", timeout=8)
    except Exception:
        pass
```

#### 3-2. 지수 백오프 + 지터
```python
import time, random

def _get_with_retry(url: str, max_retries: int = 3) -> Optional[requests.Response]:
    for attempt in range(max_retries):
        try:
            resp = _session.get(url, timeout=15)
            if resp.status_code == 403:
                # 차단 시 대기 후 재시도
                wait = (2 ** attempt) + random.uniform(0.5, 1.5)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except requests.Timeout:
            time.sleep(1 + random.uniform(0, 1))
        except Exception:
            break
    return None
```

#### 3-3. 요청 간 랜덤 딜레이
```python
# 연속 요청 시 0.3~1.2초 랜덤 딜레이
time.sleep(random.uniform(0.3, 1.2))
```

#### 3-4. User-Agent 로테이션
```python
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
]
# 요청마다 랜덤 UA 적용
```

#### 3-5. 결과 캐싱 (중복 요청 방지)
```python
import functools

@functools.lru_cache(maxsize=128)
def get_album_tracks_cached(album_id: str) -> str:
    """같은 앨범 ID 반복 요청 방지 (JSON 문자열로 캐시)."""
    ...
```

### 4순위: Playwright fallback (핵심 최적화 포함)

#### 언제 사용하나
- requests 3회 재시도 후에도 403 지속
- `music.bugs.co.kr/album/{id}` 페이지만 대상 (검색 API는 해당 없음)

#### 브라우저 싱글턴 패턴 (핵심)
```python
# bugs_playwright.py (신규 파일)
from playwright.sync_api import sync_playwright, Browser
import threading

_lock = threading.Lock()
_pw = None
_browser: Optional[Browser] = None

def _get_browser() -> Browser:
    """브라우저 인스턴스 재사용 — 요청마다 launch() 금지."""
    global _pw, _browser
    with _lock:
        if _browser is None or not _browser.is_connected():
            if _pw is None:
                _pw = sync_playwright().start()
            _browser = _pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
    return _browser

def _close_browser():
    """앱 종료 시 정리."""
    global _pw, _browser
    if _browser:
        _browser.close()
    if _pw:
        _pw.stop()
```

#### 리소스 차단 (속도 개선 핵심)
```python
def _block_resources(page):
    """이미지, 폰트, 광고 등 불필요한 리소스 차단."""
    def handler(route):
        if route.request.resource_type in ("image", "media", "font", "stylesheet"):
            route.abort()
        else:
            route.continue_()
    page.route("**/*", handler)
```

#### 전체 Playwright fallback 흐름
```python
def get_album_tracks_playwright(album_id: str) -> dict:
    browser = _get_browser()
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
        locale="ko-KR",
    )
    page = context.new_page()
    _block_resources(page)  # 이미지/폰트 차단

    try:
        page.goto(
            f"https://music.bugs.co.kr/album/{album_id}",
            wait_until="domcontentloaded",  # load 대기하지 말고 DOM만
            timeout=20000,
        )
        html = page.content()
        return _parse_from_html(html, album_id)
    finally:
        context.close()  # context만 닫고 browser는 유지
```

---

## 4. LRC 수집 우선순위 재정의

```
현재: bugs_lyrics → lrclib
개선: lrclib → bugs_lyrics → (Playwright fallback은 LRC에 불필요)
```

이유:
- `lrclib.net`은 공개 무인증 API, rate limit 없음
- Bugs lyrics API는 고정 키로 작동 — 서버 HTML 차단과 무관하게 동작
- 따라서 LRC에서는 Playwright 불필요

```python
# browse.py의 LRC 요청 흐름
async def fetch_lrc(file_path, artist, title, album):
    # 1순위: lrclib (빠름, 무료)
    result = lrclib.fetch_lrc_for_file(file_path, artist, title, album)
    if result["status"] == "ok":
        return result

    # 2순위: Bugs lyrics API (싱크 가사)
    result = bugs_lyrics.fetch_lrc_for_file(file_path, artist, title)
    if result["status"] == "ok":
        return result

    return {"status": "not_found", ...}
```

---

## 5. 메타데이터 수집 우선순위 재정의

```
앨범 상세 조회 순서:
bugs.py get_album_tracks():
  1. requests + session/retry (3회)
  2. 실패 시 → bugs_playwright.get_album_tracks_playwright()
  3. 그래도 실패 시 → {"album": {}, "tracks": []} 반환 (graceful degradation)
```

---

## 6. 구현 파일 목록

| 파일 | 변경 유형 | 내용 |
|------|----------|------|
| `metadata/bugs.py` | 수정 | Session 재사용, 재시도/딜레이, UA 로테이션, 캐싱 |
| `metadata/bugs_playwright.py` | 신규 | 브라우저 싱글턴, 리소스 차단, 앨범 상세 fallback |
| `metadata/lrclib.py` | 수정 없음 | 현재 구현 유지 |
| `metadata/bugs_lyrics.py` | 수정 없음 | 현재 구현 유지 |
| `api/browse.py` | 수정 | LRC 순서: lrclib 우선 → bugs_lyrics |
| `main.py` | 수정 | 앱 종료 시 `_close_browser()` 호출 |

---

## 7. Docker 환경 고려사항

Playwright는 Chromium 바이너리가 필요합니다.

```dockerfile
# backend/Dockerfile 추가 필요
RUN pip install playwright && playwright install chromium --with-deps
```

또는 Playwright 전용 의존성을 optional로 처리:
```python
try:
    from app.core.metadata import bugs_playwright as _pw_mod
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False
```

---

## 8. 성능 영향

| 시나리오 | 예상 소요 시간 |
|---------|--------------|
| requests 성공 (1회) | ~1-2초 |
| requests 재시도 3회 후 성공 | ~5-8초 |
| Playwright fallback | ~8-15초 (브라우저 재사용 시) |
| Playwright 최초 실행 (launch) | ~20-30초 (최초 1회만) |

브라우저를 재사용하면 2번째 요청부터 Playwright도 8-15초 수준으로 감소합니다.

---

## 9. 단기 우선 적용 (즉시 효과)

1. **`lrclib → bugs_lyrics` 순서 변경** — 코드 2줄 수정, 안정성 즉시 향상
2. **`bugs.py`에 Session + 재시도 추가** — requests 레벨에서 대부분 해결 가능
3. **Playwright 통합은 2번 적용 후 여전히 403이 지속될 때 진행**
