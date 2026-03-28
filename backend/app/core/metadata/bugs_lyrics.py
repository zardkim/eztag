"""
Bugs 뮤직 LRC 가사 가져오기.

흐름:
  1. music.bugs.co.kr/search/track?q= HTML 파싱 → track_id 획득
     ※ m.bugs.co.kr/api/getSearchList JSON API는 403 차단됨 → HTML 파싱으로 대체
  2. api.bugs.co.kr/3/tracks/{track_id}/lyrics → 가사 JSON 다운로드
  3. Bugs 고유 포맷 → 표준 LRC 변환
  4. 오디오 파일과 같은 폴더에 {stem}.lrc 저장

Bugs 가사 포맷:
  "{초}|{텍스트}＃{초}|{텍스트}＃..."
  "|" 구분자가 없으면 싱크 가사 없음 (일반 텍스트 가사)
"""
import logging
import re
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_SEARCH_TRACK_URL = "https://music.bugs.co.kr/search/track?q={query}"
# Bugs 앱 내장 고정 키 (외부 발급 없음 — Bugs 자체 앱 키)
_LYRICS_API = "http://api.bugs.co.kr/3/tracks/{track_id}/lyrics?&api_key=b2de0fbe3380408bace96a5d1a76f800"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://music.bugs.co.kr/",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _get_session() -> requests.Session:
    """bugs.py 세션 재사용 (같은 프로세스 내 쿠키 공유)."""
    try:
        from app.core.metadata.bugs import _get_session as _bugs_session
        return _bugs_session()
    except Exception:
        # fallback: 독립 세션
        s = requests.Session()
        s.headers.update(_HEADERS)
        try:
            s.get("https://music.bugs.co.kr/", timeout=8)
        except Exception:
            pass
        return s


def _normalize(s: str) -> str:
    """비교용 정규화: 소문자, 공백 정리, 특수문자 제거."""
    s = s.lower().strip()
    s = re.sub(r"[^\w\s가-힣]", "", s)
    return re.sub(r"\s+", " ", s)


def _search_track_id(artist: str, title: str) -> Optional[str]:
    """Bugs 검색 페이지 HTML 파싱으로 track_id 획득."""
    query = quote(f"{artist} {title}")
    url = _SEARCH_TRACK_URL.format(query=query)
    s = _get_session()
    try:
        resp = s.get(url, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        logger.warning(f"[bugs_lyrics] search error: {e}")
        return None

    t_norm = _normalize(title)
    a_norm = _normalize(artist)

    rows = soup.select("table.trackList tbody tr")
    if not rows:
        return None

    def _row_track_id(tr) -> str:
        tid = tr.get("trackid") or ""
        if not tid:
            cb = tr.select_one("input[type=checkbox]")
            tid = cb.get("value", "") if cb else ""
        return tid

    def _row_title(tr) -> str:
        a = tr.select_one("p.title a")
        return _normalize(a.get_text(strip=True)) if a else ""

    def _row_artist(tr) -> str:
        a = tr.select_one("p.artist a")
        return _normalize(a.get_text(strip=True)) if a else ""

    # 1순위: 제목 + 아티스트 일치
    for tr in rows:
        if _row_title(tr) == t_norm:
            row_artist = _row_artist(tr)
            if a_norm in row_artist or row_artist in a_norm:
                tid = _row_track_id(tr)
                if tid:
                    return tid

    # 2순위: 제목만 일치
    for tr in rows:
        if _row_title(tr) == t_norm:
            tid = _row_track_id(tr)
            if tid:
                return tid

    # 3순위: 첫 번째 결과
    tid = _row_track_id(rows[0])
    return tid if tid else None


def _fetch_raw_lyrics(track_id: str) -> Optional[str]:
    """Bugs lyrics API 호출 → 원본 가사 문자열 반환."""
    url = _LYRICS_API.format(track_id=track_id)
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning(f"[bugs_lyrics] lyrics fetch error (id={track_id}): {e}")
        return None

    result = data.get("result")
    if not result:
        return None
    return result.get("lyrics")


def _convert_to_lrc(raw: str) -> Optional[str]:
    """Bugs 가사 포맷 → 표준 LRC 포맷 변환.

    입력: "{초}|{텍스트}＃{초}|{텍스트}＃..."
    출력: "[MM:SS.xx]텍스트\\n..."
    """
    raw = raw.replace("＃", "\n").strip()
    lines = [l for l in raw.split("\n") if l.strip()]

    lrc_lines = []
    for line in lines:
        sep = line.rfind("|")
        if sep == -1:
            continue
        time_str = line[:sep].strip()
        text = line[sep + 1:]
        try:
            t = float(time_str)
        except ValueError:
            continue

        total_sec = int(t)
        mm = total_sec // 60
        ss = total_sec % 60
        frac = round(t - total_sec, 2)
        xx = f"{frac:.2f}"[1:]  # ".00" 형태

        lrc_lines.append(f"[{mm:02d}:{ss:02d}{xx}]{text}")

    return "\n".join(lrc_lines) if lrc_lines else None


def fetch_lrc_for_file(file_path: str, artist: str, title: str) -> dict:
    """단일 오디오 파일에 대한 LRC를 Bugs에서 가져와 같은 폴더에 저장.

    Returns:
        {
            "status": "ok" | "no_sync" | "not_found" | "error",
            "lrc_path": str | None,
            "message": str | None,
        }
    """
    p = Path(file_path)
    lrc_path = p.with_suffix(".lrc")

    track_id = _search_track_id(artist, title)
    if not track_id:
        return {"status": "not_found", "lrc_path": None, "message": "트랙을 찾을 수 없습니다"}

    raw = _fetch_raw_lyrics(track_id)
    if not raw:
        return {"status": "not_found", "lrc_path": None, "message": "가사를 찾을 수 없습니다"}

    if "|" not in raw:
        return {"status": "no_sync", "lrc_path": None, "message": "싱크 가사를 지원하지 않습니다"}

    lrc_content = _convert_to_lrc(raw)
    if not lrc_content:
        return {"status": "no_sync", "lrc_path": None, "message": "가사 변환 실패"}

    try:
        lrc_path.write_text(lrc_content, encoding="utf-8")
        logger.info(f"[bugs_lyrics] saved: {lrc_path}")
        return {"status": "ok", "lrc_path": str(lrc_path), "message": None}
    except Exception as e:
        logger.error(f"[bugs_lyrics] save error ({lrc_path}): {e}")
        return {"status": "error", "lrc_path": None, "message": str(e)}
