"""
Bugs 뮤직 LRC 가사 가져오기.

흐름:
  1. m.bugs.co.kr 검색 API → track_id 획득 (기존 bugs.py와 동일한 엔드포인트)
  2. api.bugs.co.kr/3/tracks/{track_id}/lyrics → 가사 JSON 다운로드
  3. Bugs 고유 포맷 → 표준 LRC 변환
  4. 오디오 파일과 같은 폴더에 {stem}.lrc 저장

Bugs 가사 포맷:
  "{초}|{텍스트}＃{초}|{텍스트}＃..."
  "|" 구분자가 없으면 싱크 가사 없음 (일반 텍스트 가사)
"""
import logging
import os
import re
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_SEARCH_API = "https://m.bugs.co.kr/api/getSearchList"
# Bugs 모바일 앱 공개 키 — 환경변수 BUGS_API_KEY 또는 DB config bugs_api_key로 재정의 가능
_BUGS_API_KEY_DEFAULT = os.getenv("BUGS_API_KEY", "b2de0fbe3380408bace96a5d1a76f800")
_LYRICS_API = "http://api.bugs.co.kr/3/tracks/{track_id}/lyrics?&api_key={api_key}"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://music.bugs.co.kr",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
}


def _normalize(s: str) -> str:
    """비교용 정규화: 소문자, 공백 정리, 특수문자 제거."""
    s = s.lower().strip()
    s = re.sub(r"[^\w\s가-힣]", "", s)
    return re.sub(r"\s+", " ", s)


def _search_track_id(artist: str, title: str) -> Optional[str]:
    """Bugs 검색 API로 track_id 획득. 아티스트+제목 일치 우선, 없으면 제목만 일치."""
    query = f"{artist} {title}"
    try:
        resp = requests.get(
            _SEARCH_API,
            params={"type": "track", "query": query, "page": 1, "size": 20},
            headers=_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        items = resp.json().get("list", [])
    except Exception as e:
        logger.warning(f"[bugs_lyrics] search error: {e}")
        return None

    if not items:
        return None

    t_norm = _normalize(title)
    a_norm = _normalize(artist)

    # 1순위: 제목 + 아티스트 완전 일치
    for item in items:
        item_title = _normalize(item.get("title") or "")
        item_artists = _normalize(
            ", ".join(x.get("artist_nm", "") for x in item.get("artists", []))
        )
        if item_title == t_norm and (a_norm in item_artists or item_artists in a_norm):
            return str(item["track_id"])

    # 2순위: 제목만 일치
    for item in items:
        if _normalize(item.get("title") or "") == t_norm:
            return str(item["track_id"])

    # 3순위: 첫 번째 결과 (fallback)
    return str(items[0]["track_id"]) if items[0].get("track_id") else None


def _fetch_raw_lyrics(track_id: str, api_key: Optional[str] = None) -> Optional[str]:
    """Bugs lyrics API 호출 → 원본 가사 문자열 반환."""
    url = _LYRICS_API.format(track_id=track_id, api_key=api_key or _BUGS_API_KEY_DEFAULT)
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
    # ＃(전각 #) 을 줄 구분자로 치환
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
        # 소수 2자리 (hundredths)
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

    # track_id 검색
    track_id = _search_track_id(artist, title)
    if not track_id:
        return {"status": "not_found", "lrc_path": None, "message": "트랙을 찾을 수 없습니다"}

    # 가사 원본 가져오기
    raw = _fetch_raw_lyrics(track_id)
    if not raw:
        return {"status": "not_found", "lrc_path": None, "message": "가사를 찾을 수 없습니다"}

    # 싱크 가사 여부 확인
    if "|" not in raw:
        return {"status": "no_sync", "lrc_path": None, "message": "싱크 가사를 지원하지 않습니다"}

    # LRC 변환
    lrc_content = _convert_to_lrc(raw)
    if not lrc_content:
        return {"status": "no_sync", "lrc_path": None, "message": "가사 변환 실패"}

    # 파일 저장
    try:
        lrc_path.write_text(lrc_content, encoding="utf-8")
        logger.info(f"[bugs_lyrics] saved: {lrc_path}")
        return {"status": "ok", "lrc_path": str(lrc_path), "message": None}
    except Exception as e:
        logger.error(f"[bugs_lyrics] save error ({lrc_path}): {e}")
        return {"status": "error", "lrc_path": None, "message": str(e)}
