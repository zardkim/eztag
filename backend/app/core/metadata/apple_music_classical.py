"""
Apple Music Classical 메타데이터 검색.
- 검색:    https://classical.music.apple.com/{storefront}/search?term={query}
- 앨범 상세: https://classical.music.apple.com/{storefront}/album/{id}
인증 불필요 (공개 페이지).

클래식 전용 추가 필드: work_name, movement_name, movement, movement_total, composer
"""
import json
import logging
import re
import threading
from typing import Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_BASE = "https://classical.music.apple.com"
_SEARCH_URL = f"{_BASE}/{{storefront}}/search?term={{query}}"
_ALBUM_URL  = f"{_BASE}/{{storefront}}/album/{{album_id}}"
_HOME_URL   = "https://music.apple.com/"  # 클래식 앱 홈이 없으므로 Apple Music 홈 사용

_GENERIC_GENRES = {
    "music", "musik", "musique", "musica", "música", "muzyka", "musiikki",
    "musikk", "ミュージック", "음악", "classical", "클래식",
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://classical.music.apple.com/",
}

# ── 세션 싱글턴 (쿠키 유지) ──────────────────────────────────────────────────
_session_lock = threading.Lock()
_session: Optional[requests.Session] = None
_session_warmed = False


def _get_session() -> requests.Session:
    """쿠키가 설정된 세션 반환. 최초 1회만 홈 방문."""
    global _session, _session_warmed
    with _session_lock:
        if _session is None:
            _session = requests.Session()
            _session.headers.update(_HEADERS)
        if not _session_warmed:
            try:
                _session.get(_HOME_URL, timeout=8)
                _session_warmed = True
            except Exception:
                pass
    return _session


# ── 공통 헬퍼 ────────────────────────────────────────────────────────────────

def _fetch(url: str) -> Optional[BeautifulSoup]:
    s = _get_session()
    try:
        resp = s.get(url, timeout=15)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        logger.warning(f"Apple Music Classical fetch error ({url}): {e}")
        return None


def _get_server_data(soup: BeautifulSoup) -> dict:
    script = soup.find("script", id="serialized-server-data")
    if not script:
        return {}
    try:
        raw = json.loads(script.get_text())
        if isinstance(raw, dict) and "data" in raw:
            entries = raw["data"]
        elif isinstance(raw, list):
            entries = raw
        else:
            return {}
        return entries[0] if entries else {}
    except Exception as e:
        logger.debug(f"Apple Music Classical JSON parse error: {e}")
        return {}


def _get_ldjson(soup: BeautifulSoup) -> dict:
    for tag_id in ("schema:music-album", "schema:song"):
        script = soup.find("script", {"id": tag_id})
        if script:
            try:
                return json.loads(script.get_text())
            except Exception:
                pass
    return {}


def _build_cover_url(artwork: dict, size: str = "600x600bb.jpg") -> str:
    if not artwork:
        return ""
    url_template = (
        artwork.get("dictionary", {}).get("url")
        or artwork.get("url", "")
        or artwork.get("template", "")
    )
    if not url_template:
        return ""
    url = re.sub(r'\{w\}x\{h\}[^.]*\.\{f\}', size, url_template)
    if "{" in url:
        url = re.sub(r'/[^/]+$', '', url_template) + f"/{size}"
    return url


def _extract_year(date_str: str) -> Optional[int]:
    if date_str and len(date_str) >= 4 and date_str[:4].isdigit():
        return int(date_str[:4])
    return None


def _filter_genres(genres: list) -> list:
    return [g for g in genres if g.lower() not in _GENERIC_GENRES]


def _artist_from_subtitle(subtitle_links: list) -> str:
    if not subtitle_links:
        return ""
    names = []
    for link in subtitle_links:
        title = link.get("title", "")
        if title and title not in (
            "Various Artists", "여러 아티스트", "多位艺人", "多位藝人",
            "Vários Artistas", "Verschiedene Interpreten",
        ):
            names.append(title)
    return ", ".join(names)


# ── 검색 ─────────────────────────────────────────────────────────────────────

def search_albums(query: str, storefront: str = "kr", limit: int = 10, **kwargs) -> list[dict]:
    """Apple Music Classical 앨범 검색."""
    url = _SEARCH_URL.format(storefront=storefront, query=quote(query))
    soup = _fetch(url)
    if not soup:
        return []
    entry = _get_server_data(soup)
    if not entry:
        return []

    sections = entry.get("data", {}).get("sections", [])
    results = []

    for section in sections:
        item_kind = section.get("itemKind", "")
        if item_kind not in ("squareLockup",):
            continue

        for item in section.get("items", []):
            cd = item.get("contentDescriptor") or {}
            if cd.get("kind") != "album":
                continue

            album_id = str(cd.get("identifiers", {}).get("storeAdamID", ""))
            if not album_id:
                m = re.search(r'/(\d+)(?:\?.*)?$', cd.get("url", ""))
                album_id = m.group(1) if m else ""

            title_links = item.get("titleLinks") or []
            title = (title_links[0].get("title") if title_links else None) or item.get("title") or ""
            artist = _artist_from_subtitle(item.get("subtitleLinks") or [])
            cover_url = _build_cover_url(item.get("artwork") or {})

            # url이 classical.music.apple.com 형태인지 확인
            item_url = cd.get("url", "")
            if not item_url.startswith("http"):
                item_url = f"{_BASE}{item_url}"

            results.append({
                "provider":     "apple_music_classical",
                "type":         "album",
                "provider_id":  album_id,
                "apple_url":    item_url,
                "title":        title,
                "artist":       artist,
                "album_artist": artist,
                "cover_url":    cover_url,
                "total_tracks": item.get("trackCount"),
            })

            if len(results) >= limit:
                return results

    return results


def search_tracks(query: str, storefront: str = "kr", limit: int = 10, **kwargs) -> list[dict]:
    """Apple Music Classical 트랙 검색."""
    url = _SEARCH_URL.format(storefront=storefront, query=quote(query))
    soup = _fetch(url)
    if not soup:
        return []
    entry = _get_server_data(soup)
    if not entry:
        return []

    sections = entry.get("data", {}).get("sections", [])
    results = []

    for section in sections:
        if section.get("itemKind") != "trackLockup":
            continue

        for item in section.get("items", []):
            cd = item.get("contentDescriptor") or {}
            if cd.get("kind") not in ("song", "musicVideo"):
                continue

            track_id = str(cd.get("identifiers", {}).get("storeAdamID", ""))
            title = item.get("title") or ""
            artist = item.get("artistName") or _artist_from_subtitle(item.get("subtitleLinks") or [])
            artwork = item.get("artwork") or {}

            item_url = cd.get("url", "")
            if not item_url.startswith("http"):
                item_url = f"{_BASE}{item_url}"

            results.append({
                "provider":     "apple_music_classical",
                "type":         "track",
                "provider_id":  track_id,
                "apple_url":    item_url,
                "title":        title,
                "artist":       artist,
                "cover_url":    _build_cover_url(artwork),
                "track_no":     item.get("trackNumber"),
                "disc_no":      item.get("discNumber"),
                "work_name":    item.get("workName"),
                "movement_name": item.get("movementName"),
                "explicit":     bool(item.get("showExplicitBadge")),
            })

            if len(results) >= limit:
                return results

    return results


# ── 앨범 상세 ─────────────────────────────────────────────────────────────────

def get_album_tracks(album_id: str, storefront: str = "kr") -> dict:
    """앨범 ID로 상세 정보 + 트랙 목록 반환."""
    url = _ALBUM_URL.format(storefront=storefront, album_id=album_id)
    soup = _fetch(url)
    if not soup:
        return {"album": {}, "tracks": []}
    ld = _get_ldjson(soup)
    entry = _get_server_data(soup)

    album, tracks = _parse_album_page(entry, ld, album_id, storefront)
    return {"album": album, "tracks": tracks}


def _parse_album_page(entry: dict, ld: dict, album_id: str, storefront: str) -> tuple:
    album_info: dict = {
        "provider":    "apple_music_classical",
        "provider_id": album_id,
        "apple_url":   f"{_BASE}/{storefront}/album/{album_id}",
    }

    # ld+json에서 기본 정보
    if ld:
        date = ld.get("datePublished", "")
        if date:
            album_info["release_date"] = date[:10]
            album_info["year"] = _extract_year(date)

        genres = ld.get("genre", [])
        filtered = _filter_genres(genres)
        album_info["genre"] = ", ".join(filtered[:2]) if filtered else (genres[0] if genres else "")

        desc = ld.get("description", "")
        if desc:
            copy_match = re.search(r'[℗©]\s*\d+\s*(.+?)(?:\.|$)', desc)
            if copy_match:
                album_info["label"] = copy_match.group(1).strip()

    tracks: list = []
    if not entry:
        return album_info, tracks

    data = entry.get("data", {})
    sections = data.get("sections", [])

    seo_date = data.get("seoData", {}).get("musicReleaseDate", "")
    if seo_date and not album_info.get("release_date"):
        album_info["release_date"] = seo_date[:10]
        album_info["year"] = _extract_year(seo_date)

    og_songs = data.get("seoData", {}).get("ogSongs", [])
    isrc_list = [s.get("attributes", {}).get("isrc", "") for s in og_songs]

    track_idx = 0

    for section in sections:
        item_kind = section.get("itemKind", "")

        # 앨범 헤더
        if item_kind == "containerDetailHeaderLockup":
            for item in section.get("items", []):
                cd = item.get("contentDescriptor") or {}
                if cd.get("kind") != "album":
                    continue

                album_info.setdefault("title", item.get("title", ""))
                artwork = item.get("artwork") or {}
                album_info.setdefault("cover_url", _build_cover_url(artwork))

                tc = item.get("trackCount")
                if tc:
                    album_info["total_tracks"] = tc

                artist = _artist_from_subtitle(item.get("subtitleLinks") or [])
                if not artist:
                    mpd = item.get("modalPresentationDescriptor") or {}
                    hs = mpd.get("headerSubtitle", "") or ""
                    artist = re.sub(r'\s*·\s*\d+.*$', '', hs).strip()
                album_info.setdefault("album_artist", artist)
                album_info.setdefault("artist", artist)

        # 트랙 목록
        elif item_kind == "trackLockup":
            # 섹션 레벨 work_name (work header)
            section_header = section.get("header") or {}
            section_item = section_header.get("item") or {}
            section_work = section_item.get("title", "")
            section_movement_total = len(section.get("items", []))

            for movement_idx, item in enumerate(section.get("items", []), start=1):
                cd = item.get("contentDescriptor") or {}
                if cd.get("kind") not in ("song", "musicVideo"):
                    continue

                t: dict = {
                    "provider":        "apple_music_classical",
                    "album_title":     album_info.get("title", ""),
                    "album_artist":    album_info.get("album_artist", ""),
                    "cover_url":       album_info.get("cover_url", ""),
                    "release_date":    album_info.get("release_date", ""),
                    "year":            album_info.get("year"),
                    "genre":           album_info.get("genre", ""),
                    "label":           album_info.get("label", ""),
                    "total_tracks":    album_info.get("total_tracks"),
                    "title":           item.get("title", ""),
                    "explicit":        bool(item.get("showExplicitBadge")),
                }

                track_no = item.get("trackNumber")
                if track_no:
                    t["track_no"] = track_no

                disc_no = item.get("discNumber")
                if disc_no:
                    t["disc_no"] = disc_no

                duration = item.get("duration")
                if duration:
                    t["duration_ms"] = duration

                # 작곡가
                composer = item.get("composer") or item.get("composerName", "")
                if composer:
                    t["composer"] = composer

                # Work / Movement (클래식 전용)
                work_name = item.get("workName") or section_work
                if work_name:
                    t["work_name"] = work_name

                movement_name = item.get("movementName") or item.get("title", "")
                if movement_name and work_name:
                    t["movement_name"] = movement_name

                if work_name:
                    t["movement"] = item.get("movementNumber") or movement_idx
                    t["movement_total"] = item.get("movementCount") or section_movement_total

                artist_name = item.get("artistName") or _artist_from_subtitle(item.get("subtitleLinks") or [])
                t["artist"] = artist_name or album_info.get("album_artist", "")

                if track_idx < len(isrc_list) and isrc_list[track_idx]:
                    t["isrc"] = isrc_list[track_idx]
                track_idx += 1

                if t.get("title"):
                    tracks.append(t)

    for i, t in enumerate(tracks):
        if "track_no" not in t:
            t["track_no"] = i + 1

    return album_info, tracks
