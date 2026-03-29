"""
LRCLIB LRC 싱크 가사 가져오기.

흐름:
  1. https://lrclib.net/api/search?track_name=...&artist_name=... → 검색
  2. synced_lyrics 필드 사용 (이미 표준 LRC 포맷)
  3. 오디오 파일과 같은 폴더에 {stem}.lrc 저장

LRCLIB API:
  GET https://lrclib.net/api/search
  params: track_name, artist_name, album_name, q
  응답: [{id, name, artist_name, album_name, duration, instrumental, plain_lyrics, synced_lyrics}, ...]
"""
import logging
import re
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_SEARCH_API = "https://lrclib.net/api/search"
_GET_API = "https://lrclib.net/api/get"

_HEADERS = {
    "User-Agent": "eztag/1.0 (https://github.com/eztag)",
    "Accept": "application/json",
}


def _normalize(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s가-힣]", "", s)
    return re.sub(r"\s+", " ", s)


def _search(artist: str, title: str, album: str = "") -> Optional[str]:
    """LRCLIB 검색 → synced_lyrics 반환."""
    params = {"track_name": title, "artist_name": artist}
    if album:
        params["album_name"] = album

    try:
        resp = requests.get(_SEARCH_API, params=params, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        items = resp.json()
    except Exception as e:
        logger.warning(f"[lrclib] search error: {e}")
        return None

    if not items:
        return None

    t_norm = _normalize(title)
    a_norm = _normalize(artist)

    # LRCLIB API 응답은 camelCase 필드명 사용 (syncedLyrics, artistName, trackName)
    # 1순위: 제목+아티스트 일치 + syncedLyrics 있음
    for item in items:
        if item.get("instrumental"):
            continue
        item_artist = item.get("artistName") or ""
        item_title  = item.get("trackName") or item.get("name") or ""
        if (
            _normalize(item_title) == t_norm
            and (a_norm in _normalize(item_artist)
                 or _normalize(item_artist) in a_norm)
            and item.get("syncedLyrics")
        ):
            return item["syncedLyrics"]

    # 2순위: 제목 일치 + syncedLyrics 있음
    for item in items:
        if item.get("instrumental"):
            continue
        item_title = item.get("trackName") or item.get("name") or ""
        if _normalize(item_title) == t_norm and item.get("syncedLyrics"):
            return item["syncedLyrics"]

    # 3순위: 첫 번째 결과에 syncedLyrics 있음
    for item in items:
        if item.get("syncedLyrics"):
            return item["syncedLyrics"]

    return None


def fetch_lrc_for_file(file_path: str, artist: str, title: str, album: str = "") -> dict:
    """단일 오디오 파일에 대한 LRC를 LRCLIB에서 가져와 같은 폴더에 저장.

    Returns:
        {
            "status": "ok" | "no_sync" | "not_found" | "error",
            "lrc_path": str | None,
            "message": str | None,
        }
    """
    p = Path(file_path)
    lrc_path = p.with_suffix(".lrc")

    synced = _search(artist, title, album)
    if not synced:
        return {"status": "not_found", "lrc_path": None, "message": "트랙을 찾을 수 없습니다"}

    try:
        lrc_path.write_text(synced, encoding="utf-8")
        logger.info(f"[lrclib] saved: {lrc_path}")
        return {"status": "ok", "lrc_path": str(lrc_path), "message": None}
    except Exception as e:
        logger.error(f"[lrclib] save error ({lrc_path}): {e}")
        return {"status": "error", "lrc_path": None, "message": str(e)}
