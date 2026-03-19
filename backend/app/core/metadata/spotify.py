"""
Spotify Web API를 이용한 메타데이터 검색.
인증: Client Credentials Flow (사용자 로그인 불필요).
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _get_client(client_id: str, client_secret: str):
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        auth = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret,
        )
        return spotipy.Spotify(auth_manager=auth)
    except Exception as e:
        logger.error(f"[spotify] Client init failed: {e}")
        return None


def _seconds(ms: Optional[int]) -> Optional[float]:
    return round(ms / 1000, 2) if ms else None


def _parse_track(item: dict) -> dict:
    """Spotify track 항목 → 표준 메타데이터 딕셔너리."""
    album = item.get("album", {})
    artists = item.get("artists", [])
    album_artists = album.get("artists", [])

    images = album.get("images", [])
    cover_url = images[0]["url"] if images else None

    release_date = album.get("release_date", "")
    year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None

    external_ids = item.get("external_ids", {})

    return {
        "source": "spotify",
        "spotify_id": item.get("id"),
        "spotify_url": item.get("external_urls", {}).get("spotify"),
        "title": item.get("name"),
        "artist": ", ".join(a["name"] for a in artists),
        "album_artist": ", ".join(a["name"] for a in album_artists) if album_artists else None,
        "album_title": album.get("name"),
        "album_type": album.get("album_type"),          # album / single / compilation
        "track_no": item.get("track_number"),
        "disc_no": item.get("disc_number"),
        "total_tracks": album.get("total_tracks"),
        "year": year,
        "release_date": release_date,                   # 전체 날짜 (예: 2021-04-16)
        "duration": _seconds(item.get("duration_ms")),
        "cover_url": cover_url,
        "genre": None,  # Spotify track API는 장르를 직접 제공하지 않음 (artist API 별도)
        "explicit": item.get("explicit", False),
        "popularity": item.get("popularity"),           # 0-100
        "isrc": external_ids.get("isrc"),
        "preview_url": item.get("preview_url"),
    }


def _parse_album(item: dict) -> dict:
    """Spotify album 항목 → 표준 메타데이터 딕셔너리."""
    artists = item.get("artists", [])
    images = item.get("images", [])
    cover_url = images[0]["url"] if images else None
    release_date = item.get("release_date", "")
    year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None

    return {
        "source": "spotify",
        "spotify_id": item.get("id"),
        "spotify_url": item.get("external_urls", {}).get("spotify"),
        "album_title": item.get("name"),
        "album_artist": ", ".join(a["name"] for a in artists),
        "album_type": item.get("album_type"),           # album / single / compilation
        "year": year,
        "release_date": release_date,
        "cover_url": cover_url,
        "total_tracks": item.get("total_tracks"),
        "genres": item.get("genres", []),               # 검색 결과에는 보통 비어있음 (full album에만 있음)
        "label": item.get("label"),                     # full album fetch 시에만 반환
        "popularity": item.get("popularity"),
    }


def search_tracks(query: str, client_id: str, client_secret: str, limit: int = 5) -> list[dict]:
    """트랙 검색. 결과: 표준 메타데이터 리스트 (아티스트 장르 보완)."""
    sp = _get_client(client_id, client_secret)
    if not sp:
        return []
    try:
        results = sp.search(q=query, type="track", limit=limit, market="KR")
        items = results.get("tracks", {}).get("items", [])
        parsed = [_parse_track(t) for t in items]

        # 아티스트 장르 일괄 조회 (unique artist IDs)
        artist_id_map: dict[str, str] = {}
        for item in items:
            for a in item.get("artists", []):
                if a.get("id"):
                    artist_id_map[a["id"]] = a["id"]
        unique_ids = list(artist_id_map.keys())[:5]  # 최대 5명
        if unique_ids:
            try:
                artist_data = sp.artists(unique_ids)
                genre_map: dict[str, str] = {}
                for ad in artist_data.get("artists", []):
                    genres = ad.get("genres", [])
                    if genres:
                        genre_map[ad["id"]] = genres[0]
                # 각 트랙에 장르 적용
                for item, meta in zip(items, parsed):
                    for a in item.get("artists", []):
                        if a.get("id") in genre_map:
                            meta["genre"] = genre_map[a["id"]]
                            break
            except Exception:
                pass

        return parsed
    except Exception as e:
        logger.error(f"[spotify] Track search error: {e}")
        return []


def search_albums(query: str, client_id: str, client_secret: str, limit: int = 5) -> list[dict]:
    """앨범 검색. 결과: 표준 메타데이터 리스트 (full album으로 genres/label 보완)."""
    sp = _get_client(client_id, client_secret)
    if not sp:
        return []
    try:
        results = sp.search(q=query, type="album", limit=limit, market="KR")
        items = results.get("albums", {}).get("items", [])
        album_ids = [a["id"] for a in items if a.get("id")]
        # albums() API는 최대 20개까지 batch 조회 가능
        if album_ids:
            full = sp.albums(album_ids)
            full_items = full.get("albums", [])
            parsed = [_parse_album(a) for a in full_items if a]
        else:
            parsed = [_parse_album(a) for a in items]

        # 장르가 없는 앨범은 아티스트 장르로 보완 (Spotify는 장르를 아티스트에 저장)
        no_genre_indices = [i for i, p in enumerate(parsed) if not p.get("genres")]
        if no_genre_indices:
            # 장르 없는 앨범의 첫 번째 아티스트 ID 수집
            artist_ids = []
            for i in no_genre_indices:
                orig = (full_items if album_ids else items)[i] if i < len(full_items if album_ids else items) else None
                if orig:
                    for a in orig.get("artists", []):
                        if a.get("id"):
                            artist_ids.append((i, a["id"]))
                            break
            # batch 조회 (최대 50개)
            unique_ids = list({aid for _, aid in artist_ids})
            if unique_ids:
                try:
                    artist_data = sp.artists(unique_ids[:50])
                    genre_map = {}
                    for ad in artist_data.get("artists", []):
                        genres = ad.get("genres", [])
                        if genres:
                            genre_map[ad["id"]] = genres[0]
                    for idx, aid in artist_ids:
                        if aid in genre_map:
                            parsed[idx]["genres"] = [genre_map[aid]]
                except Exception:
                    pass

        return parsed
    except Exception as e:
        logger.error(f"[spotify] Album search error: {e}")
        return []


def get_track_by_id(spotify_id: str, client_id: str, client_secret: str) -> Optional[dict]:
    """Spotify Track ID로 상세 정보 조회. 장르는 아티스트 API에서 가져옴."""
    sp = _get_client(client_id, client_secret)
    if not sp:
        return None
    try:
        track = sp.track(spotify_id)
        meta = _parse_track(track)

        # 아티스트 장르 보완
        artist_ids = [a["id"] for a in track.get("artists", []) if a.get("id")]
        if artist_ids:
            artist_data = sp.artist(artist_ids[0])
            genres = artist_data.get("genres", [])
            if genres:
                meta["genre"] = genres[0]

        return meta
    except Exception as e:
        logger.error(f"[spotify] Get track by ID error: {e}")
        return None


def get_album_tracks(spotify_album_id: str, client_id: str, client_secret: str) -> list[dict]:
    """앨범의 트랙 목록 조회."""
    sp = _get_client(client_id, client_secret)
    if not sp:
        return []
    try:
        album = sp.album(spotify_album_id)
        album_meta = _parse_album(album)
        tracks = album.get("tracks", {}).get("items", [])
        # 장르: 앨범 genres 또는 아티스트 genres 사용
        genres = album_meta.get("genres") or []
        genre = genres[0] if genres else None

        result = []
        for t in tracks:
            # album_tracks API item에는 album 정보가 없으므로 album_meta에서 보완
            meta = {
                "source": "spotify",
                "spotify_id": t.get("id"),
                "spotify_url": t.get("external_urls", {}).get("spotify"),
                "title": t.get("name"),
                "artist": ", ".join(a["name"] for a in t.get("artists", [])),
                "album_artist": album_meta.get("album_artist"),
                "album_title": album_meta.get("album_title"),
                "album_type": album_meta.get("album_type"),
                "track_no": t.get("track_number"),
                "disc_no": t.get("disc_number"),
                "total_tracks": album_meta.get("total_tracks"),
                "year": album_meta.get("year"),
                "release_date": album_meta.get("release_date"),
                "duration": _seconds(t.get("duration_ms")),
                "cover_url": album_meta.get("cover_url"),
                "genre": genre,
                "label": album_meta.get("label"),
                "explicit": t.get("explicit", False),
                "isrc": t.get("external_ids", {}).get("isrc"),
                "preview_url": t.get("preview_url"),
            }
            result.append(meta)
        return result
    except Exception as e:
        logger.error(f"[spotify] Get album tracks error: {e}")
        return []
