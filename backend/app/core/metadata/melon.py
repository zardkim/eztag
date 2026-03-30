"""
Melon 메타데이터 검색.
- 앨범 검색: https://www.melon.com/search/album/index.htm?q={query}  (HTML 스크래핑)
- 트랙 검색: https://www.melon.com/search/song/index.htm?q={query}   (HTML 스크래핑)
- 앨범 상세: https://www.melon.com/album/detail.htm?albumId={id}      (HTML 스크래핑)
인증 불필요 (공개 페이지).
"""
import logging
import re
import threading
from typing import Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_BASE = "https://www.melon.com"
_SEARCH_ALBUM_URL = f"{_BASE}/search/album/index.htm?q={{query}}"
_SEARCH_TRACK_URL = f"{_BASE}/search/song/index.htm?q={{query}}"
_ALBUM_URL        = f"{_BASE}/album/detail.htm?albumId={{album_id}}"
_HOME_URL         = f"{_BASE}/"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Referer": "https://www.melon.com/",
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

def _clean_text(el) -> str:
    """태그의 직접 텍스트 노드만 추출 — screen_out 등 자식 태그 텍스트 제외."""
    if not el:
        return ""
    from bs4 import NavigableString
    return " ".join(
        str(c).strip() for c in el.children
        if isinstance(c, NavigableString) and str(c).strip()
    )


_HIDDEN_CLS = re.compile(r'screen_out|blind|sr.only|hidden', re.I)

def _artist_links(el) -> list:
    """숨김 부모(screen_out 등) 안의 링크를 제외한 아티스트 <a> 목록."""
    if not el:
        return []
    return [a for a in el.find_all("a") if not a.find_parent(class_=_HIDDEN_CLS)]


def _artist_text(el) -> str:
    """요소에서 중복 없이 아티스트명 추출."""
    if not el:
        return ""
    links = _artist_links(el)
    if links:
        seen, parts = set(), []
        for a in links:
            t = _clean_text(a) or a.get_text(strip=True)
            if t and t not in seen:
                seen.add(t)
                parts.append(t)
        return ", ".join(parts)
    return _clean_text(el) or el.get_text(strip=True)


def _fetch(url: str) -> Optional[BeautifulSoup]:
    s = _get_session()
    try:
        resp = s.get(url, timeout=15)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        logger.warning(f"Melon fetch error ({url}): {e}")
        return None


def _extract_album_id(href: str) -> str:
    m = re.search(r"goAlbumDetail\(['\"]?(\d+)['\"]?\)", href)
    return m.group(1) if m else ""


def _cover_hires(url: str) -> str:
    """멜론 커버 URL의 resize 파라미터를 500으로 교체."""
    if not url:
        return ""
    url = re.sub(r'resize/\d+', 'resize/500', url)
    return url.split("?")[0] if "?" in url else url


def _extract_year(date_str: str) -> Optional[int]:
    if date_str and len(date_str) >= 4 and date_str[:4].isdigit():
        return int(date_str[:4])
    return None


def _parse_album_type(raw: str) -> str:
    """[EP], [싱글], [정규], [OST] 등 → album_type 값."""
    low = raw.lower()
    if "ep" in low or "미니" in low:
        return "ep"
    if "싱글" in low or "single" in low:
        return "single"
    if "ost" in low or "사운드트랙" in low:
        return "soundtrack"
    if "컴필" in low or "compilation" in low:
        return "compilation"
    return "album"


# ── 검색 ─────────────────────────────────────────────────────────────────────

def search_albums(query: str, limit: int = 10, **kwargs) -> list[dict]:
    """Melon 앨범 검색."""
    url = _SEARCH_ALBUM_URL.format(query=quote(query))
    soup = _fetch(url)
    if not soup:
        return []

    results = []
    album_list = soup.find("div", class_="d_album_list")
    if not album_list:
        return []

    for item in album_list.find_all("li", class_="album11_li"):
        # 앨범 ID
        thumb_a = item.find("a", class_="thumb")
        if not thumb_a:
            continue
        album_id = _extract_album_id(thumb_a.get("href", "") or thumb_a.get("onclick", ""))
        if not album_id:
            continue

        # 앨범명
        dt = item.find("dt")
        title_a = dt.find("a", class_="ellipsis") if dt else None
        title = title_a.get_text(strip=True) if title_a else ""

        # 앨범 타입
        type_span = item.find("span", class_="vdo_name")
        album_type = _parse_album_type(type_span.get_text(strip=True)) if type_span else "album"

        # 아티스트
        artist_dd = item.find("dd", class_="atistname")
        artist = _artist_text(artist_dd)

        # 커버
        img = item.find("img")
        cover_url = _cover_hires(img.get("src", "") if img else "")

        # 발매일 (dd 텍스트에서 연도 추출)
        release_date = ""
        year = None
        for dd in item.find_all("dd"):
            text = dd.get_text(strip=True)
            m = re.search(r'(\d{4})\.(\d{2})\.(\d{2})', text)
            if m:
                release_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                year = int(m.group(1))
                break

        results.append({
            "provider":     "melon",
            "type":         "album",
            "provider_id":  album_id,
            "melon_url":    f"{_ALBUM_URL.format(album_id=album_id)}",
            "title":        title,
            "artist":       artist,
            "album_artist": artist,
            "cover_url":    cover_url,
            "album_type":   album_type,
            "release_date": release_date,
            "year":         year,
        })

        if len(results) >= limit:
            break

    return results


def search_tracks(query: str, limit: int = 10, **kwargs) -> list[dict]:
    """Melon 트랙 검색."""
    url = _SEARCH_TRACK_URL.format(query=quote(query))
    soup = _fetch(url)
    if not soup:
        return []

    results = []
    song_list = soup.find("div", class_="d_song_list")
    if not song_list:
        return []

    tbody = song_list.find("tbody")
    if not tbody:
        return []

    for row in tbody.find_all("tr"):
        # 트랙 ID
        cb = row.find("input", class_="input_check")
        track_id = cb.get("value", "") if cb else ""

        # 트랙명
        title_a = row.find("a", class_="fc_gray")
        title = title_a.get_text(strip=True) if title_a else ""
        if not title:
            continue

        # 아티스트
        artist_div = row.find("div", id="artistName") or row.find("div", class_="wrapArtistName")
        artist = _artist_text(artist_div)

        # 앨범명 + ID
        album_title = ""
        album_id = ""
        for a in row.find_all("a"):
            href = a.get("href", "") or a.get("onclick", "")
            if "goAlbumDetail" in href:
                album_title = a.get_text(strip=True)
                album_id = _extract_album_id(href)
                break

        # 커버 (썸네일)
        img = row.find("img")
        cover_url = _cover_hires(img.get("src", "") if img else "")

        results.append({
            "provider":    "melon",
            "type":        "track",
            "provider_id": track_id,
            "title":       title,
            "artist":      artist,
            "album_title": album_title,
            "cover_url":   cover_url,
        })

        if len(results) >= limit:
            break

    return results


# ── 앨범 상세 (HTML 스크래핑) ─────────────────────────────────────────────────

def get_album_tracks(album_id: str) -> dict:
    """앨범 ID로 상세 정보 + 트랙 목록 반환."""
    url = _ALBUM_URL.format(album_id=album_id)
    soup = _fetch(url)
    if not soup:
        return {"album": {}, "tracks": []}

    album = _parse_album_info(soup, album_id)
    tracks = _parse_track_list(soup, album)
    return {"album": album, "tracks": tracks}


def _parse_album_info(soup: BeautifulSoup, album_id: str) -> dict:
    info: dict = {
        "provider":    "melon",
        "provider_id": album_id,
        "melon_url":   _ALBUM_URL.format(album_id=album_id),
    }

    # 앨범명
    name_div = soup.find("div", class_="song_name")
    if name_div:
        for tag in name_div.find_all("strong"):
            tag.decompose()
        info["title"] = name_div.get_text(strip=True)

    # 아티스트
    artist_wrap = soup.find("div", class_="artist") or soup.find("a", class_="artist_name")
    if artist_wrap:
        info["album_artist"] = _artist_text(artist_wrap)
        info["artist"] = info["album_artist"]

    # 커버
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if "cdnimg.melon.co.kr" in src and "album/images" in src:
            info["cover_url"] = _cover_hires(src)
            break

    # 메타 정보 (발매일, 장르, 발매사, 기획사)
    meta_dl = soup.find("dl", class_="list")
    if meta_dl:
        dts = meta_dl.find_all("dt")
        dds = meta_dl.find_all("dd")
        for dt, dd in zip(dts, dds):
            key = dt.get_text(strip=True)
            val = dd.get_text(" ", strip=True)
            if key == "발매일":
                date_str = val.replace(".", "-").rstrip("-")
                info["release_date"] = date_str
                info["year"] = _extract_year(date_str)
            elif key == "장르":
                info["genre"] = val
            elif key == "발매사":
                info["label"] = val
            elif key == "기획사":
                info.setdefault("label", val)

    # 앨범 타입 (제목 앞 [EP] 등 뱃지에서)
    type_span = soup.find("span", class_="vdo_name")
    if type_span:
        info["album_type"] = _parse_album_type(type_span.get_text(strip=True))

    # 앨범 소개 (있을 때만)
    intro_div = soup.find("div", id="d_video_summary") or soup.select_one("div.dtl_albuminfo")
    if intro_div:
        text = intro_div.get_text("\n", strip=True)
        if text:
            info["description"] = text

    return info


def _parse_track_list(soup: BeautifulSoup, album_info: dict) -> list[dict]:
    tracks = []
    album_artist = album_info.get("album_artist", "")
    current_disc = 1

    # 트랙 행과 디스크 헤더를 함께 순회하기 위해 tbody 전체 탐색
    tbody = soup.find("tbody", class_=re.compile(r"(d_)?track_list")) or soup.find("tbody")
    all_rows = tbody.find_all("tr") if tbody else soup.find_all("tr")

    for row in all_rows:
        if not row.get("data-group-items"):
            # 디스크 헤더 행 감지
            text = row.get_text(" ", strip=True)
            m = re.search(r'disc\s*(\d+)', text, re.IGNORECASE)
            if m:
                current_disc = int(m.group(1))
            continue

        t: dict = {
            "provider":     "melon",
            "album_title":  album_info.get("title", ""),
            "album_artist": album_artist,
            "cover_url":    album_info.get("cover_url", ""),
            "release_date": album_info.get("release_date", ""),
            "year":         album_info.get("year"),
            "genre":        album_info.get("genre", ""),
            "label":        album_info.get("label", ""),
            "disc_no":      current_disc,
        }

        # 트랙 ID
        cb = row.find("input", class_="input_check")
        if cb and cb.get("value"):
            t["provider_id"] = cb["value"]

        # 트랙 번호
        rank_span = row.find("span", class_="rank")
        if rank_span:
            txt = rank_span.get_text(strip=True)
            if txt.isdigit():
                t["track_no"] = int(txt)

        # 트랙 타이틀곡 여부
        t["is_title_track"] = bool(row.find("span", class_="bullet_icons title"))

        # 트랙명
        wrap = row.find("div", class_="wrap_song_info")
        if not wrap:
            continue
        title_div = wrap.find("div", class_="ellipsis")
        title_a = title_div.find("a") if title_div else None
        title = title_a.get_text(strip=True) if title_a else ""
        if not title:
            continue
        t["title"] = title

        # 아티스트
        artist_div = wrap.find("div", class_="rank02")
        artist = _artist_text(artist_div) if artist_div else ""
        t["artist"] = artist or album_artist

        tracks.append(t)

    # 트랙 번호 없는 경우 순서대로 부여
    for i, t in enumerate(tracks):
        if "track_no" not in t:
            t["track_no"] = i + 1

    # total_tracks
    if tracks:
        album_info["total_tracks"] = len(tracks)
        for t in tracks:
            t["total_tracks"] = len(tracks)

    return tracks
