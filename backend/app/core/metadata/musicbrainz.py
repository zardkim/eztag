"""
MusicBrainz 를 이용한 메타데이터 검색.

디스크 구성(몇 장짜리인지, 각 장이 몇 곡인지)이 정확해서 박스셋·합본에 강하다.
커버는 Cover Art Archive 에서 받는다.

인증: 없다. 대신 **1초당 1회** 제한이 IP 기준으로 엄격히 적용되고,
      넘기면 503 이 온다. 의미 있는 User-Agent 는 필수다.
"""
import logging
import re
import threading
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_API = "https://musicbrainz.org/ws/2"
_CAA = "https://coverartarchive.org"
# MusicBrainz 는 연락 가능한 UA 를 요구한다. 없으면 차단 대상이 된다.
_UA = "eztag/1.0 ( https://github.com/zardkim/eztag )"
_TIMEOUT = 20

# 1초당 1회 — 자동태그가 파일마다 순차로 검색하므로 모듈 안에서 직접 지킨다.
# 호출부에 맡기면 503 이 나고, 결과가 빈 리스트로 보여 "결과 없음" 과 구분이 안 된다.
_MIN_INTERVAL = 1.1
_lock = threading.Lock()
_last_call = 0.0

# 오디오로 취급할 매체. 박스셋에는 Blu-ray/DVD-Video 가 섞여 들어오는데
# 이걸 그대로 두면 유일한 CD 가 "디스크 4" 가 되어 실제 파일과 어긋난다.
_AUDIO_FORMATS = {
    "CD", "Digital Media", "Vinyl", "12\" Vinyl", "7\" Vinyl", "10\" Vinyl",
    "SACD", "Hybrid SACD", "Cassette", "HDCD", "DVD-Audio", "Blu-spec CD",
    "SHM-CD", "Copy Control CD", "Enhanced CD", "Minidisc", "DualDisc",
}


def _throttle() -> None:
    global _last_call
    with _lock:
        gap = time.monotonic() - _last_call
        if gap < _MIN_INTERVAL:
            time.sleep(_MIN_INTERVAL - gap)
        _last_call = time.monotonic()


def _get(path: str, params: dict) -> Optional[dict]:
    params = {**params, "fmt": "json"}
    _throttle()
    try:
        r = requests.get(f"{_API}{path}", params=params,
                         headers={"User-Agent": _UA}, timeout=_TIMEOUT)
        if r.status_code == 503:
            logger.warning("[musicbrainz] rate limited (503)")
            return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning(f"[musicbrainz] GET {path} failed: {e}")
        return None


def _credit(ac: list) -> str:
    """artist-credit 은 [{name, joinphrase}, ...] 형태로 이어 붙여야 한다."""
    out = []
    for a in ac or []:
        if not isinstance(a, dict):
            continue
        out.append(a.get("name") or (a.get("artist") or {}).get("name") or "")
        out.append(a.get("joinphrase") or "")
    return "".join(out).strip() or ", ".join(
        (a.get("name") or "") for a in (ac or []) if isinstance(a, dict)
    )


def _year(date: str) -> Optional[int]:
    try:
        y = int((date or "")[:4])
        return y if 1000 < y < 2200 else None
    except (TypeError, ValueError):
        return None


def _cover_url(mbid: str) -> str:
    """Cover Art Archive 는 없으면 404 다. 존재 확인에 요청을 또 쓰지 않고 URL 만 만든다."""
    return f"{_CAA}/release/{mbid}/front-500" if mbid else ""


def _audio_media(media: list) -> list:
    """오디오 매체만 남기고 1부터 다시 번호를 매긴다."""
    return [
        m for m in (media or [])
        if (m.get("format") or "") in _AUDIO_FORMATS and (m.get("track-count") or 0) > 0
    ]


# 에디션 수식어 — MusicBrainz 의 릴리스 제목에는 대개 들어있지 않다.
# "The Sound of Music" 은 제목이고 "45th Anniversary Edition" 은 매체 제목이라,
# 폴더명을 통째로 던지면 한 건도 안 걸린다. Discogs 는 반대로 전체 문자열이 잘 맞아
# 이 처리는 MusicBrainz 쪽에만 둔다.
_EDITION_RE = re.compile(
    r"""\b(
        \d{1,3}(st|nd|rd|th)\s+anniversary
      | anniversary(\s+(special|deluxe|collector'?s?|limited))?\s*(edition|collection)?
      | (special|deluxe|expanded|collector'?s?|limited|super\s+deluxe|platinum|gold)\s+edition
      | remaster(ed)?(\s+\d{4})?
      | original\s+(motion\s+picture\s+)?soundtrack
      | ost | bonus\s+track[s]? | reissue
      | dis[ck]\s*\d+ | cd\s*\d+
    )\b""",
    re.IGNORECASE | re.VERBOSE,
)
_PAREN_RE = re.compile(r"[\(\[][^)\]]*[\)\]]")


def _simplify(query: str) -> str:
    """에디션 수식어와 괄호 보충어를 떼어낸 핵심 제목."""
    q = _PAREN_RE.sub(" ", query)
    q = _EDITION_RE.sub(" ", q)
    q = re.sub(r"[,\-–—]+", " ", q)
    return re.sub(r"\s+", " ", q).strip()


# 'edition' 'special' 같은 일반어는 변별력이 없어 토큰에서 뺀다.
_WEAK_TOKENS = {
    "edition", "special", "deluxe", "version", "collection", "the", "a", "an",
    "original", "soundtrack", "ost", "remaster", "remastered", "reissue",
    "disc", "disk", "cd", "vol", "volume",
}


def _fielded_query(query: str) -> str:
    """
    release:"핵심제목" AND <에디션 토큰> 형태로 바꾼다.

    MusicBrainz 는 제목을 따옴표로 묶어 필드 지정해야 정확히 걸리고,
    에디션 토큰('45th', 'anniversary')을 AND 로 덧붙이면 같은 제목의 다른
    앨범(The Adicts 의 'Sound of Music' 등)을 밀어낼 수 있다.
    """
    core = _simplify(query)
    if not core:
        return ""
    escaped = core.replace('\\', '').replace('"', '')
    parts = [f'release:"{escaped}"']

    # 원문에서 핵심 제목을 빼고 남은 말 중 변별력 있는 토큰만
    rest = re.sub(re.escape(core), " ", query, flags=re.IGNORECASE)
    core_words = {w.lower() for w in re.findall(r"[A-Za-z0-9가-힣]+", core)}
    tokens = [
        t for t in re.findall(r"[A-Za-z0-9가-힣]+", rest)
        if t.lower() not in _WEAK_TOKENS and t.lower() not in core_words and len(t) > 1
    ]
    parts.extend(tokens[:2])     # 2개를 넘기면 너무 좁아져 0건이 된다
    return " AND ".join(parts)


def search_albums(query: str, limit: int = 10, **kwargs) -> list[dict]:
    """
    원문과 필드 지정 쿼리 두 가지로 찾아 합친다.

    둘 중 하나만으로는 부족하다 —
      · 원문만: MusicBrainz 제목에는 'Special Edition' 같은 말이 없어서
        엉뚱한 앨범이 상위에 온다
      · 제목만: 'Sound of Music' 로는 동명의 다른 앨범(펑크 밴드 The Adicts)이
        먼저 잡힌다
    → release:"핵심제목" AND 에디션토큰 형태가 정확히 집어낸다
    요청 2회(약 2.2초)가 들지만 앨범 검색은 사용자가 직접 누르는 동작이고,
    곡 단위 자동태그는 search_tracks 를 쓰므로 영향이 없다.
    """
    raw: list[dict] = []
    seen: set[str] = set()

    # 정확한 필드 쿼리를 먼저 던진다. 순서가 곧 결과 순서다.
    queries = []
    fielded = _fielded_query(query)
    if fielded and fielded.lower() != query.lower():
        queries.append(fielded)
    queries.append(query)

    for q in queries:
        data = _get("/release/", {"query": q, "limit": limit})
        for r in (data or {}).get("releases") or []:
            mbid = r.get("id", "")
            if mbid and mbid not in seen:
                seen.add(mbid)
                raw.append(r)

    # score 로 재정렬하지 않는다 — score 는 쿼리마다 상대적이라
    # 서로 다른 쿼리의 결과를 섞어 정렬하면 엉뚱한 게 위로 올라온다.
    # 정확한 필드 쿼리를 먼저 던졌으니 그 순서를 그대로 쓴다.

    results = []
    for r in raw[:limit]:
        mbid = r.get("id", "")
        artist = _credit(r.get("artist-credit"))
        date = r.get("date", "") or ""
        audio = _audio_media(r.get("media") or [])
        label = ", ".join(
            (li.get("label") or {}).get("name", "")
            for li in (r.get("label-info") or []) if li.get("label")
        )
        results.append({
            "provider":     "musicbrainz",
            "type":         "album",
            "provider_id":  mbid,
            "title":        r.get("title", ""),
            "artist":       artist,
            "album_artist": artist,
            "album_type":   ((r.get("release-group") or {}).get("primary-type") or "album").lower(),
            "cover_url":    _cover_url(mbid),
            "release_date": date,
            "year":         _year(date),
            "country":      r.get("country"),
            "label":        label,
            "total_tracks": sum(m.get("track-count") or 0 for m in audio) or None,
            "disc_count":   len(audio) or None,
            "barcode":      r.get("barcode"),
        })
    return results


def search_tracks(query: str, limit: int = 10, **kwargs) -> list[dict]:
    data = _get("/recording/", {"query": query, "limit": limit})
    if not data:
        return []

    results = []
    for rec in (data.get("recordings") or [])[:limit]:
        artist = _credit(rec.get("artist-credit"))
        rel = (rec.get("releases") or [{}])[0]
        mbid = rel.get("id", "")
        date = rel.get("date", "") or ""
        media = (rel.get("media") or [{}])[0]
        track = (media.get("track") or [{}])[0] if media.get("track") else {}
        length = rec.get("length")
        results.append({
            "provider":     "musicbrainz",
            "provider_id":  mbid or rec.get("id", ""),
            "title":        rec.get("title", ""),
            "artist":       artist,
            "album_artist": _credit(rel.get("artist-credit")) or artist,
            "album_title":  rel.get("title", ""),
            "track_no":     track.get("number") and _int(track.get("number")),
            "disc_no":      media.get("position") or 1,
            "total_tracks": media.get("track-count"),
            "cover_url":    _cover_url(mbid),
            "release_date": date,
            "year":         _year(date),
            "duration":     round(length / 1000, 2) if length else None,
            "genre":        None,
            "isrc":         (rec.get("isrcs") or [None])[0],
        })
    return results


def _int(v) -> Optional[int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def get_album_tracks(album_id: str, **kwargs) -> dict:
    d = _get(f"/release/{album_id}", {"inc": "recordings+artist-credits+labels+release-groups"})
    if not d:
        return {"album": {}, "tracks": []}

    artist = _credit(d.get("artist-credit"))
    date = d.get("date", "") or ""
    cover = _cover_url(album_id)
    label = ", ".join(
        (li.get("label") or {}).get("name", "")
        for li in (d.get("label-info") or []) if li.get("label")
    )
    audio = _audio_media(d.get("media") or [])
    total = sum(m.get("track-count") or 0 for m in audio)

    album = {
        "provider":     "musicbrainz",
        "provider_id":  album_id,
        "title":        d.get("title", ""),
        "artist":       artist,
        "album_artist": artist,
        "album_title":  d.get("title", ""),
        "cover_url":    cover,
        "release_date": date,
        "year":         _year(date),
        "label":        label,
        "country":      d.get("country"),
        "barcode":      d.get("barcode"),
        "total_tracks": total or None,
        "disc_count":   len(audio) or None,
        "genre":        "",
    }

    tracks = []
    # 오디오 매체만 1번부터 다시 번호를 매긴다 (Blu-ray/DVD 가 섞인 박스셋 대응)
    for disc_no, m in enumerate(audio, 1):
        for t in (m.get("tracks") or []):
            rec = t.get("recording") or {}
            length = t.get("length") or rec.get("length")
            t_artist = _credit(t.get("artist-credit") or rec.get("artist-credit")) or artist
            tracks.append({
                "provider":     "musicbrainz",
                "provider_id":  album_id,
                "title":        t.get("title") or rec.get("title", ""),
                "artist":       t_artist,
                "album_artist": artist,
                "album_title":  d.get("title", ""),
                "track_no":     _int(t.get("number")) or _int(t.get("position")),
                "disc_no":      disc_no,
                "total_tracks": total,
                "cover_url":    cover,
                "release_date": date,
                "year":         _year(date),
                "label":        label,
                "genre":        "",
                "duration":     round(length / 1000, 2) if length else None,
            })
    return {"album": album, "tracks": tracks}
