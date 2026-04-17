"""
메타데이터 검색 API.
GET  /api/metadata/search      - 통합 검색 (활성화된 provider 병렬 조회)
GET  /api/metadata/track/{id}  - 특정 트랙의 자동 검색 (제목+아티스트 쿼리)
POST /api/metadata/apply/{id}  - 검색 결과를 트랙에 적용 (파일+DB)
GET  /api/metadata/album-tracks - Spotify 앨범 트랙 목록
"""
import json
import logging
import requests as _requests
from pathlib import Path
from typing import Optional, Literal, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Track
from app.core.auth import get_current_user
from app.core.config_store import get_config
from app.core.tag_writer import write_tags
from app.core.tag_writer import write_cover as _write_cover_fn
import app.core.cache as _cache
from app.core.metadata import spotify as sp_mod
from app.core.metadata import apple_music as am_mod
from app.core.metadata import apple_music_classical as amc_mod
from app.core.metadata import melon as ml_mod
from app.core.metadata import bugs as bg_mod
from app.core.filename_parser import parse_filename_by_pattern
from app.core.metadata.matcher import find_best_match, normalize_search_query
from app.core.tag_reader import read_tags as _read_tags

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/metadata", tags=["metadata"])


# ── 헬퍼 ──────────────────────────────────────────────────────────────────

def _get_spotify_creds(db: Session) -> tuple[str, str]:
    return (
        get_config(db, "spotify_client_id") or "",
        get_config(db, "spotify_client_secret") or "",
    )


def _spotify_enabled(db: Session) -> bool:
    if get_config(db, "spotify_enabled") != "true":
        return False
    cid, secret = _get_spotify_creds(db)
    return bool(cid and secret)


# ── 엔드포인트 ────────────────────────────────────────────────────────────

@router.get("/search")
def search_metadata(
    q: str = Query(..., min_length=1),
    type: Literal["track", "album"] = Query("track"),
    provider: Optional[str] = Query(None, description="특정 provider만 (spotify/melon/bugs/apple_music). 없으면 전체"),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """
    활성화된 메타데이터 provider로 검색.
    provider 파라미터 없으면 활성화된 전체를 병렬 조회 후 합산.
    """
    results = []

    # Spotify
    if (provider is None or provider == "spotify") and _spotify_enabled(db):
        cid, secret = _get_spotify_creds(db)
        try:
            if type == "track":
                items = sp_mod.search_tracks(q, cid, secret, limit)
            else:
                items = sp_mod.search_albums(q, cid, secret, limit)
            results.extend(items)
        except Exception as e:
            logger.warning(f"Spotify search error: {e}")

    # Apple Music
    if (provider is None or provider == "apple_music") and get_config(db, "apple_music_enabled") == "true":
        storefront = get_config(db, "apple_music_storefront") or "kr"
        if type == "track":
            results.extend(am_mod.search_tracks(q, storefront=storefront, limit=limit))
        else:
            results.extend(am_mod.search_albums(q, storefront=storefront, limit=limit))

    # Apple Music Classical
    if (provider is None or provider == "apple_music_classical") and get_config(db, "apple_music_classical_enabled") == "true":
        storefront = get_config(db, "apple_music_classical_storefront") or "us"
        if type == "track":
            results.extend(amc_mod.search_tracks(q, storefront=storefront, limit=limit))
        else:
            results.extend(amc_mod.search_albums(q, storefront=storefront, limit=limit))

    # Melon
    if (provider is None or provider == "melon") and get_config(db, "melon_enabled") == "true":
        if type == "track":
            results.extend(ml_mod.search_tracks(q))
        else:
            results.extend(ml_mod.search_albums(q))

    # Bugs (stub)
    if (provider is None or provider == "bugs") and get_config(db, "bugs_enabled") == "true":
        if type == "track":
            results.extend(bg_mod.search_tracks(q))
        else:
            results.extend(bg_mod.search_albums(q))

    return {"query": q, "type": type, "total": len(results), "results": results}


@router.get("/track/{track_id}")
def search_for_track(track_id: int, db: Session = Depends(get_db)):
    """
    DB에 있는 트랙 정보(제목+아티스트)로 자동 검색.
    프론트엔드에서 '메타데이터 검색' 버튼 클릭 시 호출.
    """
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    query = f"{track.title} {track.artist or ''}".strip()

    results = []

    if _spotify_enabled(db):
        cid, secret = _get_spotify_creds(db)
        try:
            results = sp_mod.search_tracks(query, cid, secret, limit=5)
        except Exception as e:
            logger.warning(f"Spotify search error: {e}")

    return {
        "track_id": track_id,
        "query": query,
        "results": results,
    }


@router.get("/album-tracks")
def get_album_tracks(
    spotify_album_id: Optional[str] = Query(None, description="Spotify 앨범 ID (하위 호환)"),
    provider_id: Optional[str] = Query(None, description="Provider 고유 앨범 ID"),
    provider: str = Query("spotify", description="메타데이터 소스 (spotify/bugs)"),
    db: Session = Depends(get_db),
):
    """앨범 ID로 트랙 목록 조회 (앨범 일괄 적용용)."""
    album_id = provider_id or spotify_album_id
    if not album_id:
        raise HTTPException(status_code=400, detail="provider_id 또는 spotify_album_id가 필요합니다")

    if provider == "bugs":
        if get_config(db, "bugs_enabled") != "true":
            raise HTTPException(status_code=503, detail="Bugs가 비활성화 상태입니다")
        result = bg_mod.get_album_tracks(album_id)
        return {
            "provider":    "bugs",
            "provider_id": album_id,
            "album":       result.get("album", {}),
            "tracks":      result.get("tracks", []),
        }

    if provider == "melon":
        if get_config(db, "melon_enabled") != "true":
            raise HTTPException(status_code=503, detail="Melon이 비활성화 상태입니다")
        result = ml_mod.get_album_tracks(album_id)
        return {
            "provider":    "melon",
            "provider_id": album_id,
            "album":       result.get("album", {}),
            "tracks":      result.get("tracks", []),
        }

    if provider == "apple_music":
        if get_config(db, "apple_music_enabled") != "true":
            raise HTTPException(status_code=503, detail="Apple Music이 비활성화 상태입니다")
        storefront = get_config(db, "apple_music_storefront") or "kr"
        result = am_mod.get_album_tracks(album_id, storefront=storefront)
        return {
            "provider":    "apple_music",
            "provider_id": album_id,
            "album":       result.get("album", {}),
            "tracks":      result.get("tracks", []),
        }

    if provider == "apple_music_classical":
        if get_config(db, "apple_music_classical_enabled") != "true":
            raise HTTPException(status_code=503, detail="Apple Music Classical이 비활성화 상태입니다")
        storefront = get_config(db, "apple_music_classical_storefront") or "us"
        result = amc_mod.get_album_tracks(album_id, storefront=storefront)
        return {
            "provider":    "apple_music_classical",
            "provider_id": album_id,
            "album":       result.get("album", {}),
            "tracks":      result.get("tracks", []),
        }

    # 기본: Spotify
    if not _spotify_enabled(db):
        raise HTTPException(status_code=503, detail="Spotify가 비활성화 상태입니다")
    cid, secret = _get_spotify_creds(db)
    tracks = sp_mod.get_album_tracks(album_id, cid, secret)
    return {"provider": "spotify", "spotify_album_id": album_id, "tracks": tracks}


class ApplyMetaBody(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    album_artist: Optional[str] = None
    album_title: Optional[str] = None
    track_no: Optional[int] = None
    disc_no: Optional[int] = None
    total_tracks: Optional[int] = None
    year: Optional[int] = None
    release_date: Optional[str] = None
    genre: Optional[str] = None
    label: Optional[str] = None
    cover_url: Optional[str] = None  # 커버 URL → 파일 임베드 + 앨범 covers 폴더 저장
    spotify_id: Optional[str] = None


@router.post("/apply/{track_id}")
def apply_metadata(track_id: int, body: ApplyMetaBody, db: Session = Depends(get_db)):
    """
    검색 결과를 트랙에 적용.
    1. 파일 태그 업데이트 (total_tracks, release_date, label 포함)
    2. DB 업데이트
    3. cover_url이 있으면 커버 다운로드 → 파일에 임베드 + 앨범 covers 폴더 저장
    """
    from app.core.tag_writer import write_cover as _write_cover
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    updates = body.model_dump(exclude_none=True, exclude={"cover_url", "spotify_id"})

    if updates:
        ok = write_tags(track.file_path, updates)
        if not ok:
            raise HTTPException(status_code=500, detail="파일 태그 저장 실패")
        for k, v in updates.items():
            if hasattr(track, k):
                setattr(track, k, v)

    # 단일 트랙 apply 시 커버도 함께 처리 (applyToMatchingTrack 단건용)
    if body.cover_url:
        try:
            import requests as _req
            from pathlib import Path as _Path
            resp = _req.get(body.cover_url, timeout=15)
            resp.raise_for_status()
            img_data = resp.content
            content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
            # Front Cover(type 3)만 교체 (write_cover 내부에서 처리)
            ok = _write_cover(track.file_path, img_data, content_type, 3)
            if ok:
                track.has_cover = True
            else:
                logger.error(f"write_cover returned False for {track.file_path}")
                track.has_cover = False
            # 오디오 파일 폴더에 cover.jpg/cover.png 저장 (기존 파일 삭제 후)
            ext = "png" if "png" in content_type else "jpg"
            dir_path = _Path(track.file_path).parent
            for old_name in ("cover.jpg", "cover.png", "folder.jpg", "folder.png",
                             "front.jpg", "front.png", "back.jpg", "back.png"):
                try:
                    old_f = dir_path / old_name
                    if old_f.exists():
                        old_f.unlink()
                except Exception:
                    pass
            try:
                (dir_path / f"cover.{ext}").write_bytes(img_data)
            except Exception as e:
                logger.warning(f"Cover file save failed: {e}")
        except Exception as e:
            logger.error(f"Cover download/embed failed: {e}")

    db.commit()
    db.refresh(track)
    _cache.invalidate_for_file(track.file_path)
    return {"ok": True, "track_id": track_id, "has_cover": track.has_cover}


class ApplyByPathBody(BaseModel):
    path: str
    title: Optional[str] = None
    artist: Optional[str] = None
    album_artist: Optional[str] = None
    album_title: Optional[str] = None
    track_no: Optional[int] = None
    disc_no: Optional[int] = None
    total_tracks: Optional[int] = None
    year: Optional[int] = None
    release_date: Optional[str] = None
    genre: Optional[str] = None
    label: Optional[str] = None
    cover_url: Optional[str] = None


@router.post("/apply-by-path")
def apply_metadata_by_path(
    body: ApplyByPathBody,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """파일 경로 기반으로 메타데이터 적용 (스캔 여부 무관)."""
    updates = body.model_dump(exclude_none=True, exclude={"path", "cover_url"})

    if updates:
        ok = write_tags(body.path, updates)
        if not ok:
            raise HTTPException(status_code=500, detail="파일 태그 저장 실패")

    track = db.query(Track).filter(Track.file_path == body.path).first()
    if track:
        for k, v in updates.items():
            if hasattr(track, k):
                setattr(track, k, v)
        db.commit()

    if body.cover_url:
        try:
            import requests as _req
            from pathlib import Path as _Path
            from app.core.tag_writer import write_cover as _write_cover
            resp = _req.get(body.cover_url, timeout=15)
            resp.raise_for_status()
            img_data = resp.content
            content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
            ok = _write_cover(body.path, img_data, content_type, 3)
            if ok and track:
                track.has_cover = True
            ext = "png" if "png" in content_type else "jpg"
            dir_path = _Path(body.path).parent
            for old_name in ("cover.jpg", "cover.png", "folder.jpg", "folder.png",
                             "front.jpg", "front.png", "back.jpg", "back.png"):
                try:
                    old_f = dir_path / old_name
                    if old_f.exists():
                        old_f.unlink()
                except Exception:
                    pass
            try:
                (dir_path / f"cover.{ext}").write_bytes(img_data)
            except Exception as e:
                logger.warning(f"Cover file save failed: {e}")
        except Exception as e:
            logger.warning(f"Cover download/embed failed: {e}")

    if track:
        db.commit()
    _cache.invalidate_for_file(body.path)
    return {"ok": True, "path": body.path}


class ApplyAlbumCoverBody(BaseModel):
    album_id: int
    cover_url: str


@router.post("/apply-album-cover")
def apply_album_cover(
    body: ApplyAlbumCoverBody,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    앨범 커버 URL을 한 번 다운로드해서:
    1. [최우선] covers 폴더에 저장 + album.cover_path 업데이트 (DB 커밋)
    2. 오디오 파일이 있는 폴더에 cover.jpg 저장
    3. 앨범 내 모든 트랙 오디오 파일에 커버 임베드
    """
    from app.core.tag_writer import write_cover as _write_cover
    from app.models import Album
    from pathlib import Path
    import requests as _req

    album = db.query(Album).filter(Album.id == body.album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    # 커버 이미지 1회 다운로드
    try:
        resp = _req.get(body.cover_url, timeout=15)
        resp.raise_for_status()
        img_data = resp.content
        content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"커버 다운로드 실패: {e}")

    ext = "png" if "png" in content_type else "jpg"

    # 오디오 파일 폴더에 cover.jpg 저장 + 파일 임베드
    tracks = db.query(Track).filter(Track.album_id == body.album_id).all()
    embedded = 0
    saved_dirs: set = set()

    for track in tracks:
        # 오디오 폴더에 cover.jpg 저장 (폴더당 1회)
        track_dir = str(Path(track.file_path).parent)
        if track_dir not in saved_dirs:
            dir_path = Path(track_dir)
            for old_name in ("cover.jpg", "cover.png", "folder.jpg", "folder.png",
                             "front.jpg", "front.png", "back.jpg", "back.png"):
                try:
                    old_file = dir_path / old_name
                    if old_file.exists():
                        old_file.unlink()
                except Exception:
                    pass
            try:
                (dir_path / f"cover.{ext}").write_bytes(img_data)
                saved_dirs.add(track_dir)
            except Exception as e:
                logger.warning(f"cover.{ext} save failed at {track_dir}: {e}")

        # 오디오 파일에 커버 임베드 (Front Cover만 교체)
        try:
            ok = _write_cover(track.file_path, img_data, content_type, 3)
            if ok:
                track.has_cover = True
                embedded += 1
            else:
                logger.error(f"write_cover returned False for {track.file_path}")
            _cache.invalidate_for_file(track.file_path)
        except Exception as e:
            logger.error(f"Cover embed failed for {track.file_path}: {e}")

    db.commit()
    return {
        "ok": True,
        "album_id": body.album_id,
        "embedded": embedded,
        "total": len(tracks),
    }


# ── 파일명 자동태그 ────────────────────────────────────────────────────────

def _search_tracks_by_providers(q: str, providers: list, db: Session) -> list:
    """활성화된 provider에서 트랙 검색 후 결과 합산."""
    results = []
    if "spotify" in providers and _spotify_enabled(db):
        cid, secret = _get_spotify_creds(db)
        try:
            results.extend(sp_mod.search_tracks(q, cid, secret, limit=5))
        except Exception as e:
            logger.warning(f"Spotify search error for '{q}': {e}")
    if "apple_music" in providers and get_config(db, "apple_music_enabled") == "true":
        try:
            sf = get_config(db, "apple_music_storefront") or "kr"
            results.extend(am_mod.search_tracks(q, storefront=sf, limit=5))
        except Exception as e:
            logger.warning(f"Apple Music search error for '{q}': {e}")
    if "apple_music_classical" in providers and get_config(db, "apple_music_classical_enabled") == "true":
        try:
            sf = get_config(db, "apple_music_classical_storefront") or "us"
            results.extend(amc_mod.search_tracks(q, storefront=sf, limit=5))
        except Exception as e:
            logger.warning(f"Apple Music Classical search error for '{q}': {e}")
    if "melon" in providers and get_config(db, "melon_enabled") == "true":
        try:
            results.extend(ml_mod.search_tracks(q))
        except Exception as e:
            logger.warning(f"Melon search error for '{q}': {e}")
    if "bugs" in providers and get_config(db, "bugs_enabled") == "true":
        try:
            results.extend(bg_mod.search_tracks(q))
        except Exception as e:
            logger.warning(f"Bugs search error for '{q}': {e}")
    return results


_AUTO_TAG_WRITE_FIELDS = {
    "title", "artist", "album_artist", "album_title",
    "track_no", "disc_no", "total_tracks", "year", "release_date",
    "genre", "label",
}


class AutoTagByFilenameRequest(BaseModel):
    paths: List[str]
    pattern: str
    providers: List[str]
    match_threshold: float = 70.0


class FileAutoTagResult(BaseModel):
    path: str
    filename: str
    parsed: dict
    status: str          # applied | no_match | parse_error | error
    matched_title: Optional[str] = None
    matched_artist: Optional[str] = None
    matched_album: Optional[str] = None
    matched_year: Optional[int] = None
    matched_genre: Optional[str] = None
    matched_provider: Optional[str] = None
    original: Optional[dict] = None   # 되돌리기용 원본 태그
    error: Optional[str] = None


class RevertAutoTagRequest(BaseModel):
    items: List[dict]   # [{ path, original }]


@router.post("/auto-tag-by-filename")
def auto_tag_by_filename(
    body: AutoTagByFilenameRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """파일명 파싱 → provider 검색 → 매칭 → 태그 + 커버 자동 적용 (SSE 스트리밍)."""

    def _apply_cover(path_str: str, cover_url: str, track):
        try:
            resp = _requests.get(cover_url, timeout=15)
            resp.raise_for_status()
            img_data = resp.content
            content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
            _write_cover_fn(path_str, img_data, content_type, 3)
            ext = "png" if "png" in content_type else "jpg"
            dir_path = Path(path_str).parent
            for old_name in ("cover.jpg", "cover.png", "folder.jpg", "folder.png"):
                try:
                    old_f = dir_path / old_name
                    if old_f.exists():
                        old_f.unlink()
                except Exception:
                    pass
            try:
                (dir_path / f"cover.{ext}").write_bytes(img_data)
            except Exception as e:
                logger.warning(f"Cover file save failed: {e}")
            if track:
                track.has_cover = True
        except Exception as e:
            logger.warning(f"Cover apply failed for {path_str}: {e}")

    def generate():
        total = len(body.paths)
        search_cache: dict = {}
        summary = {"applied": 0, "kept_existing": 0, "applied_parsed": 0, "parse_error": 0, "error": 0}

        for idx, path_str in enumerate(body.paths):
            p = Path(path_str)
            filename = p.stem
            result: FileAutoTagResult

            try:
                # 1. 파일명 파싱
                parsed = parse_filename_by_pattern(filename, body.pattern)
                if not parsed or not parsed.get("title"):
                    result = FileAutoTagResult(
                        path=path_str, filename=filename, parsed=parsed or {},
                        status="parse_error", error="패턴 불일치 또는 제목 없음",
                    )
                    summary["parse_error"] = summary.get("parse_error", 0) + 1
                    yield f"data: {json.dumps({'type': 'progress', 'current': idx + 1, 'total': total, 'filename': filename, 'item': result.model_dump()})}\n\n"
                    continue

                # 2. 검색 쿼리 구성 (특수문자 정규화 후 검색)
                q_parts = []
                if parsed.get("artist"):
                    q_parts.append(normalize_search_query(parsed["artist"]))
                q_parts.append(normalize_search_query(parsed["title"]))
                query = " ".join(q_parts)

                # 3. 검색 (캐시 활용)
                cache_key = query.lower()
                if cache_key not in search_cache:
                    search_cache[cache_key] = _search_tracks_by_providers(query, body.providers, db)
                candidates = search_cache[cache_key]

                # 4. 로컬 파일 재생시간 + Track 레코드
                track = db.query(Track).filter(Track.file_path == path_str).first()
                local_duration = track.duration if track else None

                # 5. 최적 매칭 선택
                best = None
                if candidates:
                    best, _ = find_best_match(parsed, candidates, local_duration, body.match_threshold)

                if best is None:
                    # ── 미매칭: 기존 태그 유지 또는 파싱값 적용 ──
                    try:
                        existing = _read_tags(path_str)
                    except Exception:
                        existing = {}

                    if existing.get("title"):
                        # 기존 태그가 있으면 그대로 유지 (파일 미수정)
                        if track:
                            track.auto_tag_status = "no_match"
                            db.commit()
                        _cache.invalidate_for_file(path_str)
                        result = FileAutoTagResult(
                            path=path_str, filename=filename, parsed=parsed,
                            status="kept_existing",
                            matched_title=existing.get("title"),
                            matched_artist=existing.get("artist"),
                            matched_album=existing.get("album_title"),
                            matched_year=existing.get("year"),
                            matched_genre=existing.get("genre"),
                        )
                        summary["kept_existing"] = summary.get("kept_existing", 0) + 1
                    else:
                        # 기존 태그 없음 → 파싱값으로 태그 쓰기
                        parse_updates = {}
                        field_map = {
                            "title": "title", "artist": "artist",
                            "track_no": "track_no", "disc_no": "disc_no",
                            "year": "year",
                        }
                        for src, dst in field_map.items():
                            if parsed.get(src):
                                parse_updates[dst] = parsed[src]
                        if parse_updates:
                            write_tags(path_str, parse_updates)
                        if track:
                            for k, v in parse_updates.items():
                                if hasattr(track, k):
                                    setattr(track, k, v)
                            track.auto_tag_status = "no_match"
                            db.commit()
                        _cache.invalidate_for_file(path_str)
                        result = FileAutoTagResult(
                            path=path_str, filename=filename, parsed=parsed,
                            status="applied_parsed",
                            matched_title=parsed.get("title"),
                            matched_artist=parsed.get("artist"),
                        )
                        summary["applied_parsed"] = summary.get("applied_parsed", 0) + 1

                    yield f"data: {json.dumps({'type': 'progress', 'current': idx + 1, 'total': total, 'filename': filename, 'item': result.model_dump()})}\n\n"
                    continue

                # 6. 원본 태그 백업 (되돌리기용)
                try:
                    original_tags = _read_tags(path_str)
                    original = {k: original_tags.get(k) for k in _AUTO_TAG_WRITE_FIELDS}
                except Exception:
                    original = {}

                # 7. 적용할 태그 구성
                updates = {k: v for k, v in best.items() if k in _AUTO_TAG_WRITE_FIELDS and v is not None}
                if parsed.get("track_no"):
                    updates["track_no"] = parsed["track_no"]
                if parsed.get("disc_no"):
                    updates["disc_no"] = parsed["disc_no"]

                if updates:
                    ok = write_tags(path_str, updates)
                    if not ok:
                        result = FileAutoTagResult(
                            path=path_str, filename=filename, parsed=parsed,
                            status="error", error="태그 쓰기 실패",
                        )
                        summary["error"] = summary.get("error", 0) + 1
                        yield f"data: {json.dumps({'type': 'progress', 'current': idx + 1, 'total': total, 'filename': filename, 'item': result.model_dump()})}\n\n"
                        continue

                if track:
                    for k, v in updates.items():
                        if hasattr(track, k):
                            setattr(track, k, v)
                    track.auto_tag_status = "ok"
                    db.commit()

                # 8. 커버 무조건 적용
                if best.get("cover_url"):
                    _apply_cover(path_str, best["cover_url"], track)
                    if track:
                        db.commit()

                _cache.invalidate_for_file(path_str)
                result = FileAutoTagResult(
                    path=path_str, filename=filename, parsed=parsed,
                    status="applied",
                    matched_title=best.get("title"),
                    matched_artist=best.get("artist"),
                    matched_album=best.get("album_title"),
                    matched_year=best.get("year"),
                    matched_genre=best.get("genre"),
                    matched_provider=best.get("provider"),
                    original=original,
                )
                summary["applied"] = summary.get("applied", 0) + 1

            except Exception as e:
                logger.error(f"auto_tag_by_filename error for {path_str}: {e}")
                result = FileAutoTagResult(
                    path=path_str, filename=filename, parsed={},
                    status="error", error=str(e),
                )
                summary["error"] = summary.get("error", 0) + 1

            yield f"data: {json.dumps({'type': 'progress', 'current': idx + 1, 'total': total, 'filename': filename, 'item': result.model_dump()})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'summary': summary})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/revert-auto-tag")
def revert_auto_tag(
    body: RevertAutoTagRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """파일명 자동태그 되돌리기 — original 태그 값으로 복원."""
    reverted = 0
    failed = 0
    for item in body.items:
        path_str = item.get("path")
        original = item.get("original") or {}
        if not path_str or not original:
            continue
        try:
            # None 값 제외 후 복원
            restore = {k: v for k, v in original.items() if v is not None}
            if restore:
                write_tags(path_str, restore)
            # DB 복원
            track = db.query(Track).filter(Track.file_path == path_str).first()
            if track:
                for k, v in original.items():
                    if hasattr(track, k):
                        setattr(track, k, v)
                db.commit()
            _cache.invalidate_for_file(path_str)
            reverted += 1
        except Exception as e:
            logger.error(f"revert_auto_tag error for {path_str}: {e}")
            failed += 1
    return {"ok": True, "reverted": reverted, "failed": failed}
