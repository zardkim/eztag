"""
Apple Music 메타데이터 검색.
- 검색:    https://music.apple.com/{storefront}/search?term={query}  (HTML 내 JSON 파싱)
- 앨범 상세: https://music.apple.com/{storefront}/album/{id}           (HTML 내 JSON 파싱)
인증 불필요 (공개 페이지).
"""
import json
import logging
import re
from typing import Optional
from urllib.parse import quote

import requests  # _fetch 내부에서만 사용
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_BASE = "https://music.apple.com"
_SEARCH_URL = f"{_BASE}/{{storefront}}/search?term={{query}}"
_ALBUM_URL  = f"{_BASE}/{{storefront}}/album/{{album_id}}"

# 제거할 일반 장르 키워드 (다국어)
_GENERIC_GENRES = {
    "music", "musik", "musique", "musica", "música", "muzyka", "musiikki",
    "musikk", "ミュージック", "음악",
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ── 공통 헬퍼 ────────────────────────────────────────────────────────────────

def _fetch(url: str) -> Optional[BeautifulSoup]:
    """UTF-8 강제 디코딩으로 HTML 가져오기."""
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        # Apple Music은 Content-Type에 charset 없이 UTF-8 반환 → 강제 지정
        resp.encoding = "utf-8"
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        logger.warning(f"Apple Music fetch error ({url}): {e}")
        return None


def _get_server_data(soup: BeautifulSoup) -> dict:
    """serialized-server-data JSON 파싱. 최상위 entry(첫 번째 객체) 반환."""
    script = soup.find("script", id="serialized-server-data")
    if not script:
        return {}
    try:
        raw = json.loads(script.get_text())
        # {"data": [...]} 또는 [{"data": {...}}] 두 형태 모두 처리
        if isinstance(raw, dict) and "data" in raw:
            entries = raw["data"]
        elif isinstance(raw, list):
            entries = raw
        else:
            return {}
        return entries[0] if entries else {}
    except Exception as e:
        logger.debug(f"Apple Music JSON parse error: {e}")
        return {}


def _get_ldjson(soup: BeautifulSoup) -> dict:
    """schema:music-album ld+json 파싱."""
    for tag_id in ("schema:music-album", "schema:song"):
        script = soup.find("script", {"id": tag_id})
        if script:
            try:
                return json.loads(script.get_text())
            except Exception:
                pass
    return {}


def _build_cover_url(artwork: dict, size: str = "600x600bb.jpg") -> str:
    """Apple Music artwork dict → 실제 커버 URL.
    artwork 구조: {"dictionary": {"url": ".../{w}x{h}bb.{f}"}}
    또는 직접    {"url": ".../{w}x{h}bb.{f}"}
    """
    if not artwork:
        return ""
    url_template = (
        artwork.get("dictionary", {}).get("url")
        or artwork.get("url", "")
    )
    if not url_template:
        return ""
    # {w}x{h}bb.{f} → size 치환
    url = re.sub(r'\{w\}x\{h\}[^.]*\.\{f\}', size, url_template)
    # 치환 안 됐으면 마지막 경로 제거 후 덧붙이기
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
    """subtitleLinks 배열에서 아티스트 이름 추출."""
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
    """Apple Music 앨범 검색."""
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
        # 앨범 목록이 있는 squareLockup 섹션만 처리 (topSearchLockup 제외)
        if item_kind not in ("squareLockup",):
            continue

        for item in section.get("items", []):
            cd = item.get("contentDescriptor") or {}
            if cd.get("kind") != "album":
                continue

            album_id = str(cd.get("identifiers", {}).get("storeAdamID", ""))
            if not album_id:
                # URL에서 ID 추출 fallback
                m = re.search(r'/(\d+)(?:\?.*)?$', cd.get("url", ""))
                album_id = m.group(1) if m else ""

            # 제목 (titleLinks 또는 item.title)
            title_links = item.get("titleLinks") or []
            title = (title_links[0].get("title") if title_links else None) or item.get("title") or ""

            # 아티스트
            artist = _artist_from_subtitle(item.get("subtitleLinks") or [])

            # 커버
            cover_url = _build_cover_url(item.get("artwork") or {})

            results.append({
                "provider":    "apple_music",
                "type":        "album",
                "provider_id": album_id,
                "apple_url":   cd.get("url", ""),
                "title":       title,
                "artist":      artist,
                "album_artist": artist,
                "cover_url":   cover_url,
                "total_tracks": item.get("trackCount"),
            })

            if len(results) >= limit:
                return results

    return results


def search_tracks(query: str, storefront: str = "kr", limit: int = 10, **kwargs) -> list[dict]:
    """Apple Music 트랙 검색."""
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

            results.append({
                "provider":    "apple_music",
                "type":        "track",
                "provider_id": track_id,
                "apple_url":   cd.get("url", ""),
                "title":       title,
                "artist":      artist,
                "cover_url":   _build_cover_url(artwork),
                "track_no":    item.get("trackNumber"),
                "disc_no":     item.get("discNumber"),
                "explicit":    bool(item.get("showExplicitBadge")),
            })

            if len(results) >= limit:
                return results

    return results


# ── 앨범 상세 (HTML 파싱) ─────────────────────────────────────────────────────

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
        "provider":    "apple_music",
        "provider_id": album_id,
        "apple_url":   f"{_BASE}/{storefront}/album/{album_id}",
    }

    # ── ld+json에서 기본 정보 ──
    if ld:
        date = ld.get("datePublished", "")
        if date:
            album_info["release_date"] = date[:10]
            album_info["year"] = _extract_year(date)

        genres = ld.get("genre", [])
        filtered = _filter_genres(genres)
        album_info["genre"] = ", ".join(filtered[:2]) if filtered else (genres[0] if genres else "")

        # copyright → 레이블 힌트
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

    # seoData에서 릴리즈 날짜 업데이트 (더 정확)
    seo_date = data.get("seoData", {}).get("musicReleaseDate", "")
    if seo_date and not album_info.get("release_date"):
        album_info["release_date"] = seo_date[:10]
        album_info["year"] = _extract_year(seo_date)

    # ogSongs ISRC 수집
    og_songs = data.get("seoData", {}).get("ogSongs", [])
    isrc_list = [s.get("attributes", {}).get("isrc", "") for s in og_songs]

    track_idx = 0

    for section in sections:
        item_kind = section.get("itemKind", "")

        # ── 앨범 헤더 ──
        if item_kind == "containerDetailHeaderLockup":
            for item in section.get("items", []):
                cd = item.get("contentDescriptor") or {}
                if cd.get("kind") != "album":
                    continue

                album_info.setdefault("title", item.get("title", ""))

                # 커버
                artwork = item.get("artwork") or {}
                cover_url = _build_cover_url(artwork)
                album_info.setdefault("cover_url", cover_url)

                # 총 트랙수
                tc = item.get("trackCount")
                if tc:
                    album_info["total_tracks"] = tc

                # 앨범 아티스트
                artist = _artist_from_subtitle(item.get("subtitleLinks") or [])
                if not artist:
                    # modalPresentationDescriptor.headerSubtitle: "아티스트 · YYYY년"
                    mpd = item.get("modalPresentationDescriptor") or {}
                    hs = mpd.get("headerSubtitle", "") or ""
                    artist = re.sub(r'\s*·\s*\d+.*$', '', hs).strip()
                album_info.setdefault("album_artist", artist)
                album_info.setdefault("artist", artist)

        # ── 트랙 목록 ──
        elif item_kind == "trackLockup":
            for item in section.get("items", []):
                cd = item.get("contentDescriptor") or {}
                if cd.get("kind") not in ("song", "musicVideo"):
                    continue

                t: dict = {
                    "provider":     "apple_music",
                    "album_title":  album_info.get("title", ""),
                    "album_artist": album_info.get("album_artist", ""),
                    "cover_url":    album_info.get("cover_url", ""),
                    "release_date": album_info.get("release_date", ""),
                    "year":         album_info.get("year"),
                    "genre":        album_info.get("genre", ""),
                    "label":        album_info.get("label", ""),
                    "total_tracks": album_info.get("total_tracks"),
                    "title":        item.get("title", ""),
                    "explicit":     bool(item.get("showExplicitBadge")),
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

                artist_name = item.get("artistName") or _artist_from_subtitle(item.get("subtitleLinks") or [])
                t["artist"] = artist_name or album_info.get("album_artist", "")

                # ISRC (ogSongs와 순서 매칭)
                if track_idx < len(isrc_list) and isrc_list[track_idx]:
                    t["isrc"] = isrc_list[track_idx]
                track_idx += 1

                if t.get("title"):
                    tracks.append(t)

    # 트랙 번호 없는 경우 순서대로 부여
    for i, t in enumerate(tracks):
        if "track_no" not in t:
            t["track_no"] = i + 1

    return album_info, tracks
