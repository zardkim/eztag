"""
Bugs 뮤직 메타데이터 검색.
- 앨범/트랙 검색: https://music.bugs.co.kr/search/{album|track}?q=  (HTML 파싱)
  ※ m.bugs.co.kr/api/getSearchList JSON API는 403 차단됨 → HTML 파싱으로 대체
- 앨범 상세:      https://music.bugs.co.kr/album/{id}               (HTML 스크래핑)
"""
import logging
import re
import threading
import time
from typing import Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_SEARCH_TRACK_URL = "https://music.bugs.co.kr/search/track?q={query}"
_SEARCH_ALBUM_URL = "https://music.bugs.co.kr/search/album?q={query}"
_ALBUM_PAGE       = "https://music.bugs.co.kr/album/{album_id}"
_HOME_URL         = "https://music.bugs.co.kr/"
_COVER_TPL        = "https://image.bugsm.co.kr/album/images/1000/{prefix}/{album_id}.jpg"

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


def _fetch_html(url: str, timeout: int = 15) -> Optional[BeautifulSoup]:
    """세션으로 URL을 가져와 BeautifulSoup 반환."""
    s = _get_session()
    try:
        resp = s.get(url, timeout=timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        logger.warning(f"Bugs fetch error ({url}): {e}")
        return None


# ── 공통 헬퍼 ────────────────────────────────────────────────────────────────

def _cover_url(album_id: str) -> str:
    """Bugs 커버 이미지 URL 생성 (1000px)."""
    prefix = str(album_id)[:-2] if len(str(album_id)) > 2 else str(album_id)
    return _COVER_TPL.format(prefix=prefix, album_id=album_id)


def _cover_hires(src: str) -> str:
    """커버 이미지 URL을 1000px 버전으로 교체."""
    if not src:
        return ""
    src = re.sub(r"album/images/\d+", "album/images/1000", src)
    return src.split("?")[0]


def _parse_ymd(ymd: str) -> str:
    """'20170222' 또는 '2021.03.25' → '2017-02-22'"""
    ymd = str(ymd).strip().replace(".", "-")
    if re.match(r"\d{4}-\d{2}-\d{2}", ymd):
        return ymd
    if len(ymd) == 8 and ymd.isdigit():
        return f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"
    return ymd


def _extract_year(date_str: str) -> Optional[int]:
    if date_str and len(date_str) >= 4 and date_str[:4].isdigit():
        return int(date_str[:4])
    return None


def _parse_album_type(raw: str) -> str:
    low = raw.lower()
    if "싱글" in low or "single" in low:
        return "single"
    if "ep" in low or "미니" in low:
        return "ep"
    if "컴필" in low or "compilation" in low:
        return "compilation"
    return "album"


def _album_id_from_href(href: str) -> str:
    m = re.search(r"/album/(\d+)", href)
    return m.group(1) if m else ""


# ── 검색 (HTML 파싱) ─────────────────────────────────────────────────────────

def _clean_artists(links) -> str:
    """아티스트 <a> 태그 목록에서 'CONNECT 아티스트' 등 비아티스트 텍스트를 제거하고 이름 반환."""
    result = []
    for a in links:
        # href에 connect가 있으면 비아티스트 링크로 판단하여 전체 제외
        if "connect" in (a.get("href") or "").lower():
            continue
        text = a.get_text(strip=True)
        # 링크 텍스트 내의 'CONNECT 아티스트' 등 불필요 텍스트 제거
        text = re.sub(r'CONNECT\s*아티스트?', '', text, flags=re.IGNORECASE).strip()
        # Bugs UI 안내 텍스트 (스크린리더용 숨김 span) 제거
        text = re.sub(r'아티스트명\s*공간\s*초과시\s*더보기\s*버튼\s*노출', '', text).strip()
        text = re.sub(r'더보기\s*버튼\s*노출', '', text).strip()
        if text:
            result.append(text)
    return ", ".join(result)


def search_albums(query: str, limit: int = 10, **kwargs) -> list[dict]:
    """앨범명으로 Bugs 앨범 검색 — HTML 파싱 방식."""
    url = _SEARCH_ALBUM_URL.format(query=quote(query))
    soup = _fetch_html(url)
    if not soup:
        return []

    results = []
    ul = soup.select_one("ul.albumList")
    if not ul:
        return []

    for li in ul.select("li"):
        # 앨범 ID
        album_id = ""
        for a in li.find_all("a", href=True):
            album_id = _album_id_from_href(a["href"])
            if album_id:
                break
        if not album_id:
            continue

        # 앨범명
        title_el = li.select_one(".albumTitle a, a.albumTitle")
        title = title_el.get_text(strip=True) if title_el else ""

        # 아티스트 (CONNECT 아티스트 링크 제외)
        artist_links = li.select(".artistName a, p.artist a, a.artist")
        artist = _clean_artists(artist_links) if artist_links else ""
        if not artist:
            artist_el = li.select_one(".artistName a, p.artist a, a.artist")
            artist = artist_el.get_text(strip=True) if artist_el else ""

        # 앨범 타입
        type_el = li.select_one(".albumType, span.albumType")
        album_type = _parse_album_type(type_el.get_text(strip=True)) if type_el else "album"

        # 발매일
        date_el = li.select_one("time, .info-release, span.date")
        release_date = _parse_ymd(date_el.get_text(strip=True)) if date_el else ""
        year = _extract_year(release_date)

        # 커버 (검색 결과는 130px → 1000px로 교체)
        img = li.select_one("img")
        cover = _cover_hires(img["src"]) if img and img.get("src") else _cover_url(album_id)

        results.append({
            "provider":     "bugs",
            "type":         "album",
            "provider_id":  album_id,
            "title":        title,
            "artist":       artist,
            "album_artist": artist,
            "album_type":   album_type,
            "cover_url":    cover,
            "release_date": release_date,
            "year":         year,
        })

        if len(results) >= limit:
            break

    return results


def search_tracks(query: str, limit: int = 10, **kwargs) -> list[dict]:
    """곡명으로 Bugs 트랙 검색 — HTML 파싱 방식."""
    url = _SEARCH_TRACK_URL.format(query=quote(query))
    soup = _fetch_html(url)
    if not soup:
        return []

    results = []
    for tr in soup.select("table.trackList tbody tr"):
        if tr.get("rowtype") and tr.get("rowtype") != "track":
            continue

        # track_id: tr 속성 또는 checkbox value
        track_id = tr.get("trackid") or ""
        if not track_id:
            cb = tr.select_one("input[type=checkbox]")
            track_id = cb.get("value", "") if cb else ""

        # 앨범 ID: tr 속성 또는 href
        album_id = tr.get("albumid") or ""
        if not album_id:
            for a in tr.find_all("a", href=True):
                album_id = _album_id_from_href(a["href"])
                if album_id:
                    break

        # 제목
        title_a = tr.select_one("p.title a")
        title = title_a.get_text(strip=True) if title_a else ""
        if not title:
            continue

        # 아티스트 (CONNECT 아티스트 링크 제외)
        artist_p = tr.select_one("p.artist")
        if artist_p:
            artist = _clean_artists(artist_p.select("a")) or artist_p.get_text(strip=True)
        else:
            artist = ""

        # 앨범명
        album_a = tr.select_one("a.album, td.info a.album")
        album_title = album_a.get_text(strip=True) if album_a else ""

        results.append({
            "provider":    "bugs",
            "type":        "track",
            "provider_id": track_id,
            "title":       title,
            "artist":      artist,
            "album_title": album_title,
            "cover_url":   _cover_url(album_id) if album_id else "",
        })

        if len(results) >= limit:
            break

    return results


# ── 앨범 상세 (HTML 스크래핑) ─────────────────────────────────────────────────

def get_album_tracks(album_id: str) -> dict:
    """앨범 ID로 상세 정보 + 트랙 목록 반환."""
    url = _ALBUM_PAGE.format(album_id=album_id)
    soup = _fetch_html(url)
    if not soup:
        return {"album": {}, "tracks": []}

    album = _parse_album_info(soup, album_id)
    tracks = _parse_track_list(soup, album)
    return {"album": album, "tracks": tracks}


def _parse_album_info(soup: BeautifulSoup, album_id: str) -> dict:
    info: dict = {
        "provider":    "bugs",
        "provider_id": album_id,
        "cover_url":   _cover_url(album_id),
    }

    cover_img = soup.select_one("div.photos img")
    if cover_img and cover_img.get("src"):
        src = re.sub(r"album/images/\d+", "album/images/1000", cover_img["src"])
        info["cover_url"] = src.split("?")[0]

    h1 = soup.select_one("header.pgTitle h1")
    if h1:
        info["title"] = h1.get_text(strip=True)

    for row in soup.select("table.info tr"):
        th = row.select_one("th")
        td = row.select_one("td")
        if not th or not td:
            continue
        key = th.get_text(strip=True)
        val = td.get_text(" ", strip=True)

        if key == "아티스트":
            # CONNECT 아티스트 버튼 등 비아티스트 링크 제외
            artist_str = _clean_artists(td.select("a")) or val
            info["album_artist"] = artist_str
            info["artist"] = artist_str
        elif key in ("유형", "앨범유형"):
            info["album_type"] = _parse_album_type(val)
        elif key == "장르":
            genres = [a.get_text(strip=True) for a in td.select("a")]
            info["genre"] = ", ".join(genres) if genres else val
        elif key == "발매일":
            time_el = td.select_one("time")
            date_str = (time_el.get_text(strip=True) if time_el else val)
            date_str = date_str.replace(".", "-").strip().rstrip("-")
            info["release_date"] = date_str
            info["year"] = _extract_year(date_str)
        elif key == "기획사":
            info["label"] = val.strip()
        elif key == "유통사":
            info["distributor"] = val.strip()

    desc_el = soup.select_one("p.desc")
    if desc_el:
        m = re.search(r'\((\d+)\)', desc_el.get_text())
        if m:
            info["total_tracks"] = int(m.group(1))

    intro_el = (
        soup.select_one("div.albumContents span")
        or soup.select_one("div.albumDesc span")
        or soup.select_one("p#albumContents span")
        or soup.select_one("p.albumContents span")
    )
    if intro_el:
        text = intro_el.get_text("\n", strip=True)
        if text:
            info["description"] = text

    return info


def _parse_track_list(soup: BeautifulSoup, album_info: dict) -> list[dict]:
    tracks = []
    album_artist = album_info.get("album_artist", "")
    current_disc = 1

    track_rows = soup.select("tr[albumid]")

    for el in track_rows:
        rowtype = el.get("rowtype") or ""
        if rowtype and rowtype != "track":
            text = el.get_text(" ", strip=True)
            m = re.search(r'disc\s*(\d+)', text, re.IGNORECASE)
            if m:
                current_disc = int(m.group(1))
            continue

        t: dict = {
            "provider":     "bugs",
            "album_artist": album_artist,
            "album_title":  album_info.get("title", ""),
            "cover_url":    album_info.get("cover_url", ""),
            "release_date": album_info.get("release_date", ""),
            "year":         album_info.get("year"),
            "genre":        album_info.get("genre", ""),
            "label":        album_info.get("label", ""),
            "total_tracks": album_info.get("total_tracks"),
            "disc_no":      current_disc,
        }

        track_id = el.get("trackid") or ""
        if not track_id:
            cb = el.select_one("input[type=checkbox]")
            track_id = cb.get("value", "") if cb else ""
        if track_id:
            t["provider_id"] = track_id

        # 제목: p.title 하위 a 태그 우선 (a[title] 사용 시 아티스트 링크가 선택될 수 있음)
        title_p = el.select_one("p.title")
        if title_p:
            title_a = title_p.select_one("a")
            if title_a:
                title = title_a.get_text(strip=True)
                title = re.sub(r'\s*\([^)]*삽입곡[^)]*\)', '', title).strip()
                t["title"] = title

        em = el.select_one("p.trackIndex em")
        if em:
            txt = em.get_text(strip=True)
            if txt.isdigit():
                t["track_no"] = int(txt)
        t["is_title_track"] = bool(el.select_one("span.albumTitle"))

        # 아티스트: CONNECT 아티스트 링크 제외
        artist_p = el.select_one("p.artist")
        if artist_p:
            t["artist"] = _clean_artists(artist_p.select("a")) or album_artist
        else:
            t["artist"] = album_artist

        if not t.get("title"):
            continue

        tracks.append(t)

    for i, t in enumerate(tracks):
        if "track_no" not in t:
            t["track_no"] = i + 1

    return tracks
