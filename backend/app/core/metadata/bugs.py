"""
Bugs 뮤직 메타데이터 검색.
- 앨범/트랙 검색: https://m.bugs.co.kr/api/getSearchList (JSON, 인증 불필요)
- 앨범 상세:      https://music.bugs.co.kr/album/{id}     (HTML 스크래핑)
"""
import logging
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://music.bugs.co.kr",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
}

_SEARCH_API = "https://m.bugs.co.kr/api/getSearchList"
_ALBUM_PAGE = "https://music.bugs.co.kr/album/{album_id}"
_COVER_TPL  = "https://image.bugsm.co.kr/album/images/1000/{prefix}/{album_id}.jpg"


# ── 공통 헬퍼 ────────────────────────────────────────────────────────────────

def _cover_url(album_id: str) -> str:
    """Bugs 커버 이미지 URL 생성 (1000px)."""
    # 예: 20032445  →  prefix=200324
    prefix = str(album_id)[:-2] if len(str(album_id)) > 2 else str(album_id)
    return _COVER_TPL.format(prefix=prefix, album_id=album_id)


def _parse_ymd(ymd: str) -> str:
    """'20170222' → '2017-02-22'"""
    ymd = str(ymd).strip()
    if len(ymd) == 8 and ymd.isdigit():
        return f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"
    return ymd


def _extract_year(date_str: str) -> Optional[int]:
    if date_str and len(date_str) >= 4 and date_str[:4].isdigit():
        return int(date_str[:4])
    return None


# ── 검색 ─────────────────────────────────────────────────────────────────────

def search_albums(query: str, limit: int = 10, **kwargs) -> list[dict]:
    """앨범명으로 Bugs 앨범 검색 → 기본 정보 반환."""
    try:
        resp = requests.get(
            _SEARCH_API,
            params={"type": "album", "query": query, "page": 1, "size": limit},
            headers=_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning(f"Bugs album search error: {e}")
        return []

    results = []
    for item in data.get("list", []):
        album_id = str(item.get("album_id", ""))
        release_date = _parse_ymd(str(item.get("release_ymd", "")))
        artist = ", ".join(a.get("artist_nm", "") for a in item.get("artists", []))
        results.append({
            "provider":      "bugs",
            "type":          "album",
            "provider_id":   album_id,
            "title":         item.get("title", ""),
            "artist":        artist,
            "album_artist":  artist,
            "cover_url":     _cover_url(album_id),
            "release_date":  release_date,
            "year":          _extract_year(release_date),
            "total_tracks":  item.get("track_count"),
        })
    return results


def search_tracks(query: str, limit: int = 10, **kwargs) -> list[dict]:
    """곡명으로 Bugs 트랙 검색."""
    try:
        resp = requests.get(
            _SEARCH_API,
            params={"type": "track", "query": query, "page": 1, "size": limit},
            headers=_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning(f"Bugs track search error: {e}")
        return []

    results = []
    for item in data.get("list", []):
        album_id = str(item.get("album_id", ""))
        release_date = _parse_ymd(str(item.get("release_ymd", "")))
        artist = ", ".join(a.get("artist_nm", "") for a in item.get("artists", []))
        results.append({
            "provider":     "bugs",
            "type":         "track",
            "provider_id":  str(item.get("track_id", "")),
            "title":        item.get("title", ""),
            "artist":       artist,
            "album_title":  item.get("album_title", ""),
            "cover_url":    _cover_url(album_id) if album_id else "",
            "release_date": release_date,
            "year":         _extract_year(release_date),
        })
    return results


# ── 앨범 상세 (HTML 스크래핑) ─────────────────────────────────────────────────

def get_album_tracks(album_id: str) -> dict:
    """앨범 ID로 상세 정보 + 트랙 목록 반환."""
    url = _ALBUM_PAGE.format(album_id=album_id)
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Bugs album page error (id={album_id}): {e}")
        return {"album": {}, "tracks": []}

    soup = BeautifulSoup(resp.text, "lxml")
    album = _parse_album_info(soup, album_id)
    tracks = _parse_track_list(soup, album)
    return {"album": album, "tracks": tracks}


def _parse_album_info(soup: BeautifulSoup, album_id: str) -> dict:
    info: dict = {
        "provider":    "bugs",
        "provider_id": album_id,
        "cover_url":   _cover_url(album_id),
    }

    # 커버 URL (페이지 이미지 URL → 1000px 치환)
    cover_img = soup.select_one("div.photos img")
    if cover_img and cover_img.get("src"):
        src = cover_img["src"]
        src = re.sub(r"album/images/\d+", "album/images/1000", src)
        src = src.split("?")[0]
        info["cover_url"] = src

    # 앨범명
    h1 = soup.select_one("header.pgTitle h1")
    if h1:
        info["title"] = h1.get_text(strip=True)

    # info 테이블 파싱
    for row in soup.select("table.info tr"):
        th = row.select_one("th")
        td = row.select_one("td")
        if not th or not td:
            continue
        key = th.get_text(strip=True)
        val = td.get_text(" ", strip=True)

        if key == "아티스트":
            artists = [a.get_text(strip=True) for a in td.select("a")]
            artist_str = ", ".join(artists) if artists else val
            info["album_artist"] = artist_str
            info["artist"] = artist_str

        elif key in ("유형", "앨범유형"):
            low = val.lower()
            if "싱글" in low:
                info["album_type"] = "single"
            elif "ep" in low or "미니" in low:
                info["album_type"] = "ep"
            elif "컴필" in low or "compilation" in low:
                info["album_type"] = "compilation"
            else:
                info["album_type"] = "album"

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

    # 총 트랙수 — "(N)" 패턴으로 추출
    desc_el = soup.select_one("p.desc")
    if desc_el:
        m = re.search(r'\((\d+)\)', desc_el.get_text())
        if m:
            info["total_tracks"] = int(m.group(1))

    # 앨범 소개 / 리뷰 (실제 구조: div.albumDesc > div.albumContents > span)
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

    # lxml은 HTML 속성명을 소문자로 정규화 (albumId → albumid)
    track_rows = soup.select("tr[albumid]")

    for el in track_rows:
        # rowtype 속성이 있을 때 disc 헤더 감지 후 track 외 행 건너뜀
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

        # Bugs 내부 트랙 ID (trackid 속성 또는 checkbox value)
        track_id = el.get("trackid") or ""
        if not track_id:
            cb = el.select_one("input[type=checkbox]")
            track_id = cb.get("value", "") if cb else ""
        if track_id:
            t["provider_id"] = track_id

        # 트랙 제목 (title 속성 → 삽입곡 설명 제거)
        title_a = el.select_one("a[title]")
        if title_a:
            title = title_a.get("title", "").strip()
            title = re.sub(r'\s*\([^)]*삽입곡[^)]*\)', '', title).strip()
            t["title"] = title

        # 트랙 번호
        em = el.select_one("p.trackIndex em")
        if em:
            txt = em.get_text(strip=True)
            if txt.isdigit():
                t["track_no"] = int(txt)

        # 아티스트
        artist_p = el.select_one("p.artist")
        if artist_p:
            artists = [a.get_text(strip=True) for a in artist_p.select("a")]
            t["artist"] = ", ".join(artists) if artists else artist_p.get_text(strip=True)
        else:
            t["artist"] = album_artist

        # 제목이 없는 행은 건너뜀
        if not t.get("title"):
            continue

        tracks.append(t)

    # 트랙 번호 없는 경우 순서대로 부여
    for i, t in enumerate(tracks):
        if "track_no" not in t:
            t["track_no"] = i + 1

    return tracks
