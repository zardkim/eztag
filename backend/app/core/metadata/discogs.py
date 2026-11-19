"""
Discogs API 를 이용한 메타데이터 검색.

외국 앨범 — 특히 재발매 / 기념반 / 박스셋 카탈로그가 가장 촘촘하다.
("Sound of Music 45th Anniversary Special Edition" 같은 제목이 그대로 검색된다)

인증: 개인 토큰은 선택이다. 없어도 검색·상세·커버가 모두 동작하며,
      레이트리밋만 25/분 → 60/분 으로 올라간다.
"""
import logging
import re
import threading
import time
from typing import Optional
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

_API = "https://api.discogs.com"
_UA = "eztag/1.0 (+https://github.com/zardkim/eztag)"
_TIMEOUT = 15

# 비인증 25/분 = 2.4초당 1회. 안전하게 간격을 둔다.
# (토큰이 있으면 60/분이지만, 호출부가 토큰 유무를 모르므로 보수적으로 잡는다)
_MIN_INTERVAL = 1.2
_lock = threading.Lock()
_last_call = 0.0


def _throttle() -> None:
    """레이트리밋 초과 시 429 가 오고 결과가 빈 리스트로 보여 원인 파악이 어렵다."""
    global _last_call
    with _lock:
        gap = time.monotonic() - _last_call
        if gap < _MIN_INTERVAL:
            time.sleep(_MIN_INTERVAL - gap)
        _last_call = time.monotonic()


def _get(path: str, params: dict, token: str = "") -> Optional[dict]:
    headers = {"User-Agent": _UA}
    if token:
        headers["Authorization"] = f"Discogs token={token}"
    _throttle()
    try:
        r = requests.get(f"{_API}{path}", params=params, headers=headers, timeout=_TIMEOUT)
        if r.status_code == 429:
            logger.warning("[discogs] rate limited (429)")
            return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning(f"[discogs] GET {path} failed: {e}")
        return None


def _year(v) -> Optional[int]:
    try:
        y = int(str(v)[:4])
        return y if 1000 < y < 2200 else None
    except (TypeError, ValueError):
        return None


def _clean_artist(name: str) -> str:
    """Discogs 는 동명이인 구분용으로 'Artist (2)' / 'Artist*' 를 붙인다."""
    name = re.sub(r"\s*\(\d+\)\s*$", "", name or "")
    return name.rstrip("*").strip()


def _split_title(raw: str) -> tuple[str, str]:
    """검색 결과의 title 은 'Artist - Album' 한 덩어리로 온다."""
    if " - " in raw:
        artist, _, album = raw.partition(" - ")
        return _clean_artist(artist), album.strip()
    return "", raw.strip()


def _parse_position(pos: str) -> tuple[Optional[int], Optional[int]]:
    """
    Discogs 트랙 position → (disc_no, track_no).
      '7'     → (None, 7)
      '2-13'  → (2, 13)        여러 장짜리
      'A1'    → (1, 1)         LP 면 표기. A/B=1장, C/D=2장 …
    """
    pos = (pos or "").strip()
    if not pos:
        return None, None
    m = re.fullmatch(r"(\d+)\s*[-.]\s*(\d+)", pos)
    if m:
        return int(m.group(1)), int(m.group(2))
    if pos.isdigit():
        return None, int(pos)
    m = re.fullmatch(r"([A-Za-z])(\d+)", pos)
    if m:
        side = m.group(1).upper()
        return (ord(side) - ord("A")) // 2 + 1, int(m.group(2))
    return None, None


def _cover_from(d: dict) -> str:
    imgs = d.get("images") or []
    for i in imgs:
        if i.get("type") == "primary" and i.get("uri"):
            return i["uri"]
    return imgs[0].get("uri", "") if imgs else (d.get("cover_image") or d.get("thumb") or "")


def search_albums(query: str, limit: int = 10, token: str = "", **kwargs) -> list[dict]:
    """앨범 검색. 폴더명을 그대로 던져도 잘 맞는 편이다."""
    data = _get("/database/search", {"q": query, "type": "release", "per_page": limit}, token)
    if not data:
        return []

    results = []
    for r in (data.get("results") or [])[:limit]:
        artist, album = _split_title(r.get("title", ""))
        fmts = r.get("format") or []
        results.append({
            "provider":     "discogs",
            "type":         "album",
            "provider_id":  str(r.get("id", "")),
            "title":        album,
            "artist":       artist,
            "album_artist": artist,
            "album_type":   "compilation" if "Compilation" in fmts else "album",
            # 검색 결과의 cover_image 는 비어 오는 경우가 많다 — 상세 조회에서 채워진다.
            "cover_url":    r.get("cover_image") or r.get("thumb") or "",
            "release_date": str(r.get("year") or ""),
            "year":         _year(r.get("year")),
            "label":        ", ".join(r.get("label") or [])[:200],
            "genre":        ", ".join(r.get("genre") or []),
            "country":      r.get("country"),
            "format":       ", ".join(fmts),
        })
    return results


def search_tracks(query: str, limit: int = 10, token: str = "", **kwargs) -> list[dict]:
    """
    Discogs 에는 트랙 단위 검색 API 가 없다.
    앨범을 찾아 그 트랙 목록에서 제목이 맞는 것을 추려 돌려준다.
    """
    albums = search_albums(query, limit=3, token=token)
    if not albums:
        return []

    needle = re.sub(r"\s+", " ", query.lower()).strip()
    out: list[dict] = []
    for alb in albums:
        detail = get_album_tracks(alb["provider_id"], token=token)
        for t in detail.get("tracks", []):
            title = (t.get("title") or "").lower()
            if title and (title in needle or needle in title):
                out.append(t)
                if len(out) >= limit:
                    return out
    return out


def get_album_tracks(album_id: str, token: str = "", **kwargs) -> dict:
    """릴리스 ID 로 앨범 정보 + 트랙 목록."""
    d = _get(f"/releases/{album_id}", {}, token)
    if not d:
        return {"album": {}, "tracks": []}

    artists = ", ".join(_clean_artist(a.get("name", "")) for a in (d.get("artists") or []))
    cover = _cover_from(d)
    genres = (d.get("genres") or []) + (d.get("styles") or [])
    labels = ", ".join(l.get("name", "") for l in (d.get("labels") or []))
    year = _year(d.get("year")) or _year(d.get("released"))

    album = {
        "provider":     "discogs",
        "provider_id":  str(album_id),
        "title":        d.get("title", ""),
        "artist":       artists,
        "album_artist": artists,
        "album_title":  d.get("title", ""),
        "cover_url":    cover,
        "release_date": str(d.get("released") or d.get("year") or ""),
        "year":         year,
        "genre":        ", ".join(genres),
        "label":        labels,
        "country":      d.get("country"),
    }

    raw = [t for t in (d.get("tracklist") or []) if t.get("type_") == "track"]
    album["total_tracks"] = len(raw)

    tracks = []
    seq = 0
    for t in raw:
        seq += 1
        disc_no, track_no = _parse_position(t.get("position", ""))
        t_artists = ", ".join(_clean_artist(a.get("name", "")) for a in (t.get("artists") or []))
        tracks.append({
            "provider":     "discogs",
            "provider_id":  str(album_id),
            "title":        t.get("title", ""),
            "artist":       t_artists or artists,
            "album_artist": artists,
            "album_title":  d.get("title", ""),
            "track_no":     track_no if track_no is not None else seq,
            "disc_no":      disc_no or 1,
            "total_tracks": len(raw),
            "cover_url":    cover,
            "release_date": album["release_date"],
            "year":         year,
            "genre":        ", ".join(genres),
            "label":        labels,
            "duration":     _duration(t.get("duration", "")),
        })

    return {"album": album, "tracks": tracks}


def _duration(s: str) -> Optional[float]:
    """'4:32' → 272.0"""
    if not s or ":" not in s:
        return None
    try:
        parts = [int(p) for p in s.split(":")]
    except ValueError:
        return None
    sec = 0
    for p in parts:
        sec = sec * 60 + p
    return float(sec)
