"""폴더 탐색 + 파일 목록 + 태그 쓰기 + 파일명 변경 API."""
import logging
import os
import re
import shutil
from pathlib import Path

_log = logging.getLogger(__name__)

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, UploadFile, File
from fastapi.responses import Response, FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.core.auth import get_current_user
from app.models.scan_folder import ScanFolder
from app.models.track import Track
from app.core.tag_writer import write_tags, write_cover, remove_cover
from app.core.tag_reader import read_tags, extract_cover, extract_cover_at, list_covers
from app.core.config_store import get_destination_folders, get_excluded_folders
import app.core.cache as _cache

router = APIRouter(prefix="/api/browse", tags=["browse"])

AUDIO_EXTS = {".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wav", ".wma"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".tif"}

# 반주/경음악 감지 패턴 (LRC 검색 및 YouTube MV 검색 건너뜀)
_INST_RE = re.compile(
    r"""
    (?:                                      # 괄호 안 패턴
        [\(\[\{]
        \s*
        (?:
            inst(?:r(?:a?u?mental?)?)?\s*(?:ver(?:sion?)?)?  # (inst), (instr), (instrumental)
            | m\.?\s*r\.?                                     # (mr), (m.r), (m.r.)
            | minus\s*one                                     # (minus one)
        )
        \s*
        [\)\]\}]
    )
    | (?:경음악|반주)                          # 한국어 단어 (괄호 없어도 감지)
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _is_instrumental(title: str) -> bool:
    """곡 제목에 반주/경음악 패턴이 포함되면 True."""
    return bool(_INST_RE.search(title))


# ── 경로 보안 검증 ──────────────────────────────────────────
def _is_under_root(p: Path, root: Path) -> bool:
    try:
        p.relative_to(root)
        return True
    except ValueError:
        return False


def _validate_path(path: str, db: Session, allow_destinations: bool = False, allow_lrc_folder: bool = False, allow_workspace: bool = False) -> Path:
    """등록된 스캔 폴더(또는 이동할 폴더) 하위 경로인지 검증."""
    import os as _os
    p = Path(path).resolve()
    roots = [Path(f.path).resolve() for f in db.query(ScanFolder).all()]
    # library_path(라이브러리 열기 피커에서 선택한 경로 허용)
    from app.core.config_store import get_library_path as _get_lib
    lib_root = _get_lib(db)
    if lib_root and lib_root.is_dir():
        roots.append(lib_root)
    if allow_destinations:
        from app.core.config_store import get_destination_folders
        for d in get_destination_folders(db):
            roots.append(Path(d["path"]).resolve())
    if allow_lrc_folder:
        from app.core.config_store import get_config
        lrc_base = get_config(db, "lrc_base_folder") or ""
        if lrc_base:
            roots.append(Path(lrc_base).resolve())
    if allow_workspace:
        from app.core.config_store import get_workspace_path
        roots.append(get_workspace_path(db))
    for root in roots:
        try:
            p.relative_to(root)
            return p
        except ValueError:
            continue
    raise HTTPException(status_code=403, detail="Path not in registered scan folders")


# ── 루트 폴더 목록 ─────────────────────────────────────────
@router.get("/roots")
def get_roots(
    with_children: bool = Query(False),
    force: bool = Query(False),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """등록된 스캔 폴더(루트 노드) 목록. with_children=true 이면 1depth 자식 포함."""
    cache_key = f"roots:wc={with_children}"
    if not force:
        cached = _cache.get_roots()
        if cached and cached.get("key") == cache_key:
            return cached["data"]

    excluded = get_excluded_folders(db)

    def _skip(name: str) -> bool:
        return name.startswith(".") or name in excluded

    folders = db.query(ScanFolder).all()
    result = []
    for f in folders:
        p = Path(f.path)
        has_children = False
        children = []
        if p.exists():
            try:
                sub_items = sorted(p.iterdir())
                has_children = any(x.is_dir() and not _skip(x.name) for x in sub_items)
                if with_children:
                    for item in sub_items:
                        if not item.is_dir() or _skip(item.name):
                            continue
                        item_has_children = False
                        item_has_audio = False
                        try:
                            sub = list(item.iterdir())
                            item_has_children = any(x.is_dir() and not _skip(x.name) for x in sub)
                            item_has_audio = any(x.is_file() and x.suffix.lower() in AUDIO_EXTS for x in sub)
                        except PermissionError:
                            pass
                        children.append({
                            "name": item.name,
                            "path": str(item),
                            "has_children": item_has_children,
                            "has_audio": item_has_audio,
                        })
            except PermissionError:
                pass
        node = {
            "id": f.id,
            "name": f.name or p.name,
            "path": f.path,
            "has_children": has_children,
            "isRoot": True,
        }
        if with_children:
            node["children"] = children
        result.append(node)

    _cache.set_roots({"key": cache_key, "data": result})
    return result


# ── 하위 디렉터리 목록 ─────────────────────────────────────
@router.get("/children")
def get_children(
    path: str = Query(...),
    force: bool = Query(False),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """지정 경로의 하위 디렉터리 목록."""
    p = _validate_path(path, db, allow_workspace=True)
    if not p.is_dir():
        raise HTTPException(status_code=400, detail="Not a directory")

    if not force:
        cached = _cache.get_children(str(p))
        if cached is not None:
            return cached

    excluded = get_excluded_folders(db)

    def _skip_c(name: str) -> bool:
        return name.startswith(".") or name in excluded

    children = []
    try:
        for item in sorted(p.iterdir()):
            if not item.is_dir() or _skip_c(item.name):
                continue
            has_children = False
            has_audio = False
            try:
                sub_items = list(item.iterdir())
                has_children = any(x.is_dir() and not _skip_c(x.name) for x in sub_items)
                has_audio = any(x.is_file() and x.suffix.lower() in AUDIO_EXTS for x in sub_items)
            except PermissionError:
                pass
            children.append({
                "name": item.name,
                "path": str(item),
                "has_children": has_children,
                "has_audio": has_audio,
            })
    except PermissionError:
        pass

    _cache.set_children(str(p), children)
    return children


# ── 폴더 내 오디오 파일 목록 ───────────────────────────────
def _scan_untracked_files(folder_path: str, untracked: list[str]) -> None:
    """백그라운드: DB에 없는 파일들의 태그를 읽어 DB에 저장하고 캐시 무효화."""
    if not untracked:
        return
    try:
        from app.database import SessionLocal
        from app.models.track import Track as _Track
        db = SessionLocal()
        try:
            for path_str in untracked:
                try:
                    item = Path(path_str)
                    if not item.is_file():
                        continue
                    # 이미 등록됐을 수 있으므로 재확인
                    if db.query(_Track).filter(_Track.file_path == path_str).first():
                        continue
                    tags = read_tags(path_str)
                    stat = item.stat()
                    track = _Track(
                        file_path=path_str,
                        file_format=tags.get("file_format", item.suffix.lstrip(".")),
                        file_size=stat.st_size,
                        modified_time=stat.st_mtime,
                        title=tags.get("title") or item.stem,
                        artist=tags.get("artist"),
                        album_artist=tags.get("album_artist"),
                        album_title=tags.get("album_title"),
                        track_no=tags.get("track_no"),
                        total_tracks=tags.get("total_tracks"),
                        disc_no=tags.get("disc_no"),
                        year=tags.get("year"),
                        release_date=tags.get("release_date"),
                        genre=tags.get("genre"),
                        label=tags.get("label"),
                        isrc=tags.get("isrc"),
                        duration=tags.get("duration"),
                        bitrate=tags.get("bitrate"),
                        sample_rate=tags.get("sample_rate"),
                        tag_version=tags.get("tag_version"),
                        comment=tags.get("comment"),
                        lyrics=tags.get("lyrics"),
                        has_cover=bool(tags.get("has_cover")),
                        has_lyrics=bool(tags.get("has_lyrics")),
                    )
                    db.add(track)
                except Exception as e:
                    _log.debug(f"[bg-scan] {path_str}: {e}")
            db.commit()
        finally:
            db.close()
    except Exception as e:
        _log.warning(f"[bg-scan] folder={folder_path}: {e}")
    finally:
        # 캐시 무효화 → 다음 요청 시 DB 데이터 반영
        _cache.invalidate_files(folder_path)


@router.get("/files")
def get_files(
    path: str = Query(...),
    force: bool = Query(False),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """지정 폴더의 오디오 파일 목록 (DB 태그 정보 포함).

    성능 최적화:
    - DB에 있는 파일은 mtime 체크 없이 즉시 DB 데이터 반환
    - DB에 없는 파일은 기본 파일 정보만 즉시 반환 (파일 열기 없음)
    - 미스캔 파일은 백그라운드에서 read_tags() 후 DB 등록
    """
    p = _validate_path(path, db, allow_workspace=True)
    if not p.is_dir():
        raise HTTPException(status_code=400, detail="Not a directory")

    if not force:
        cached = _cache.get_files(str(p))
        if cached is not None:
            return cached

    files = []
    warning = None
    untracked_paths = []  # 백그라운드 스캔 대상

    # .lrc 파일 집합: 폴더 내 한 번에 수집 (per-file stat 대신)
    try:
        lrc_set = {
            item.stem
            for item in p.iterdir()
            if item.is_file() and item.suffix.lower() == ".lrc"
        }
    except Exception:
        lrc_set = set()

    try:
        # 오디오 파일 목록
        audio_items = sorted(
            item for item in p.iterdir()
            if item.is_file() and item.suffix.lower() in AUDIO_EXTS
        )

        # DB 한 번에 조회
        tracks_map: dict[str, Track] = {}
        if audio_items:
            str_paths = [str(item) for item in audio_items]
            tracks_map = {
                t.file_path: t
                for t in db.query(Track).filter(Track.file_path.in_(str_paths)).all()
            }

        for item in audio_items:
            try:
                stat = item.stat()
            except OSError:
                continue

            track = tracks_map.get(str(item))
            has_lrc = item.stem in lrc_set

            if track:
                # ── DB 데이터 즉시 반환 (파일 열기 없음) ──
                files.append({
                    "id": track.id, "album_id": track.album_id,
                    "filename": item.name, "path": str(item),
                    "title":        track.title or item.stem,
                    "artist":       track.artist,
                    "album_artist": track.album_artist,
                    "album_title":  track.album_title,
                    "track_no":     track.track_no,
                    "total_tracks": track.total_tracks,
                    "disc_no":      track.disc_no,
                    "year":         track.year,
                    "release_date": track.release_date,
                    "genre":        track.genre,
                    "label":        track.label,
                    "isrc":         track.isrc,
                    "duration":     track.duration,
                    "bitrate":      track.bitrate,
                    "sample_rate":  track.sample_rate,
                    "tag_version":  track.tag_version,
                    "comment":      track.comment,
                    "file_format":  (track.file_format or "").upper(),
                    "has_cover":      track.has_cover,
                    "has_lyrics":     track.has_lyrics,
                    "is_title_track": bool(track.is_title_track),
                    "youtube_url":    track.youtube_url,
                    "has_lrc":      has_lrc,
                    "lyrics":       track.lyrics,
                    "file_size":    stat.st_size,
                    "modified_time": stat.st_mtime,
                    "scanned": True,
                })
            else:
                # ── 미스캔 파일: 기본 정보만 즉시 반환 ──
                files.append({
                    "id": None, "album_id": None,
                    "filename": item.name, "path": str(item),
                    "title":        item.stem,
                    "artist":       None,
                    "album_artist": None,
                    "album_title":  None,
                    "track_no":     None,
                    "total_tracks": None,
                    "disc_no":      None,
                    "year":         None,
                    "release_date": None,
                    "genre":        None,
                    "label":        None,
                    "isrc":         None,
                    "duration":     None,
                    "bitrate":      None,
                    "sample_rate":  None,
                    "tag_version":  None,
                    "comment":      None,
                    "file_format":  item.suffix.lstrip(".").upper(),
                    "has_cover":      False,
                    "has_lyrics":     False,
                    "is_title_track": False,
                    "youtube_url":    None,
                    "has_lrc":      has_lrc,
                    "lyrics":       None,
                    "file_size":    stat.st_size,
                    "modified_time": stat.st_mtime,
                    "scanned": False,
                })
                untracked_paths.append(str(item))

    except PermissionError:
        warning = "일부 항목에 접근 권한이 없습니다."

    # 이미지 / HTML 파일 수집
    extra_files = []
    try:
        for item in sorted(p.iterdir()):
            if not item.is_file():
                continue
            ext = item.suffix.lower()
            if ext in IMAGE_EXTS:
                stat = item.stat()
                extra_files.append({
                    "filename": item.name,
                    "path": str(item),
                    "file_type": "image",
                    "file_size": stat.st_size,
                    "modified_time": stat.st_mtime,
                })
            elif ext == ".html":
                stat = item.stat()
                # eztag 생성 파일 감지: 파일명 패턴 또는 generator 메타태그 확인
                is_eztag = item.name.startswith("[Info]") or item.name.startswith("[앨범카드]")
                if not is_eztag:
                    try:
                        with item.open("r", encoding="utf-8", errors="ignore") as _hf:
                            head = _hf.read(2048)
                        is_eztag = 'content="eztag"' in head
                    except Exception:
                        pass
                extra_files.append({
                    "filename": item.name,
                    "path": str(item),
                    "file_type": "html",
                    "is_eztag": is_eztag,
                    "file_size": stat.st_size,
                    "modified_time": stat.st_mtime,
                })
    except PermissionError:
        pass

    # 앨범 description 조회 (첫 번째 트랙의 album_id 기준)
    album_description = None
    for t in tracks_map.values():
        if t.album_id:
            from app.models.album import Album as AlbumModel
            alb = db.query(AlbumModel).filter(AlbumModel.id == t.album_id).first()
            if alb:
                album_description = alb.description
            break

    has_eztag_report = any(f.get("is_eztag") for f in extra_files)

    # eztag HTML 파일에서 YouTube URL 보완 (youtube_url이 없는 파일 대상)
    eztag_html = next((f for f in extra_files if f.get("is_eztag")), None)
    if eztag_html:
        from app.core.html_exporter import parse_youtube_urls_from_html
        yt_map = parse_youtube_urls_from_html(eztag_html["path"])
        if yt_map:
            for file_entry in files:
                if not file_entry.get("youtube_url") and file_entry.get("filename") in yt_map:
                    file_entry["youtube_url"] = yt_map[file_entry["filename"]]

    result = {"files": files, "extra_files": extra_files, "warning": warning, "album_description": album_description, "has_eztag_report": has_eztag_report}
    if not warning:
        _cache.set_files(str(p), result)

    # 백그라운드로 미스캔 파일 DB 등록
    if untracked_paths and background_tasks is not None:
        background_tasks.add_task(_scan_untracked_files, str(p), untracked_paths)

    return result


# ── 태그 저장 ──────────────────────────────────────────────
class WriteTagsRequest(BaseModel):
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
    lyrics: Optional[str] = None
    comment: Optional[str] = None


@router.post("/write-tags")
def write_tags_endpoint(
    req: WriteTagsRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """파일에 태그를 직접 쓰고, DB에 있으면 DB도 업데이트."""
    p = _validate_path(req.path, db, allow_workspace=True)
    if not p.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    updates = req.model_dump(exclude={"path"}, exclude_none=True)

    # 파일에 태그 쓰기
    ok = write_tags(str(p), updates)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to write tags to file")

    # DB에 있으면 DB도 업데이트
    track = db.query(Track).filter(Track.file_path == str(p)).first()
    if track:
        for field, val in updates.items():
            if hasattr(track, field):
                setattr(track, field, val)
        if "lyrics" in updates:
            track.has_lyrics = bool(updates["lyrics"])
        db.commit()
        db.refresh(track)

    _cache.invalidate_for_file(str(p))

    # 활동 로그
    from app.core.log_writer import write_activity_log
    fields_str = ", ".join(updates.keys())
    write_activity_log(db, "tag_write", f"태그 저장: {p.name} [{fields_str}]",
                       action="write_tags", file_path=str(p),
                       username=getattr(current_user, "username", None))

    return {"ok": True, "track_id": track.id if track else None}


# ── 배치 태그 저장 ─────────────────────────────────────────
class BatchWriteTagsRequest(BaseModel):
    paths: list[str]
    title: Optional[str] = None
    artist: Optional[str] = None
    album_artist: Optional[str] = None
    album_title: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    track_no: Optional[int] = None
    disc_no: Optional[int] = None
    total_tracks: Optional[int] = None
    release_date: Optional[str] = None
    label: Optional[str] = None
    lyrics: Optional[str] = None
    comment: Optional[str] = None
    clear_fields: list[str] = []


@router.post("/batch-write-tags")
def batch_write_tags_endpoint(
    req: BatchWriteTagsRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """여러 파일에 공통 태그를 쓰고, DB에 있으면 DB도 업데이트."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    updates = req.model_dump(exclude={"paths", "clear_fields"}, exclude_none=True)
    clear_fields = req.clear_fields or []
    if not updates and not clear_fields:
        raise HTTPException(status_code=422, detail="No fields to update")

    roots = [Path(f.path).resolve() for f in db.query(ScanFolder).all()]
    # _validate_path 와 동일하게 라이브러리 경로 + 워크스페이스 경로도 허용
    from app.core.config_store import get_library_path, get_workspace_path
    lib_root = get_library_path(db)
    if lib_root and lib_root.is_dir():
        roots.append(lib_root)
    ws_root = get_workspace_path(db)
    if ws_root:
        roots.append(ws_root)

    # 유효 경로 검증
    valid_paths = []
    for raw_path in req.paths:
        p = Path(raw_path).resolve()
        if any(_is_under_root(p, r) for r in roots) and p.is_file():
            valid_paths.append(p)

    if not valid_paths:
        return {"ok": True, "count": 0}

    # 파일 쓰기 병렬 처리
    written: set[str] = set()
    workers = min(8, len(valid_paths))
    with ThreadPoolExecutor(max_workers=workers) as exe:
        futures = {exe.submit(write_tags, str(p), updates, clear_fields): p for p in valid_paths}
        for fut in as_completed(futures):
            p = futures[fut]
            try:
                if fut.result():
                    written.add(str(p))
            except Exception as e:
                _log.error(f"[batch-write-tags] write_tags failed for {p}: {e}")

    # DB 업데이트: 한 번의 IN 쿼리로 일괄 조회
    str_paths = list(written)
    tracks_map = {
        t.file_path: t
        for t in db.query(Track).filter(Track.file_path.in_(str_paths)).all()
    }

    for sp in str_paths:
        track = tracks_map.get(sp)
        if not track:
            continue
        for field, val in updates.items():
            if hasattr(track, field):
                setattr(track, field, val)
        for field in clear_fields:
            if hasattr(track, field):
                setattr(track, field, None)
        if "lyrics" in updates:
            track.has_lyrics = bool(updates["lyrics"])
        elif "lyrics" in clear_fields:
            track.has_lyrics = False
        try:
            track.modified_time = Path(sp).stat().st_mtime
        except OSError:
            pass

    db.commit()
    for sp in str_paths:
        _cache.invalidate_for_file(sp)

    # 활동 로그
    from app.core.log_writer import write_activity_log
    fields_str = ", ".join(list(updates.keys()) + [f"clear:{f}" for f in clear_fields])
    write_activity_log(db, "tag_write",
                       f"일괄 태그 저장: {len(written)}개 파일 [{fields_str}]",
                       action="batch_write_tags",
                       file_path=req.paths[0] if req.paths else None,
                       username=getattr(current_user, "username", None),
                       detail=f"total={len(req.paths)}, written={len(written)}")

    return {"ok": True, "count": len(written)}


# ── 파일명 변경 ────────────────────────────────────────────
class RenameRequest(BaseModel):
    path: str
    new_name: str  # 확장자 포함


@router.post("/rename")
def rename_file(
    req: RenameRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """파일명 변경 (디스크 + DB)."""
    p = _validate_path(req.path, db, allow_workspace=True)
    if not p.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    new_name = req.new_name.strip()
    if not new_name or "/" in new_name or "\\" in new_name:
        raise HTTPException(status_code=422, detail="Invalid filename")

    new_path = p.parent / new_name
    if new_path.exists():
        raise HTTPException(status_code=409, detail="File already exists")

    # 확장자 보존 (다를 경우 원본 확장자 유지)
    if new_path.suffix.lower() not in AUDIO_EXTS:
        new_path = new_path.with_suffix(p.suffix)

    os.rename(str(p), str(new_path))

    # LRC 파일도 동일하게 변경
    lrc_old = p.with_suffix(".lrc")
    lrc_new = new_path.with_suffix(".lrc")
    if lrc_old.exists() and not lrc_new.exists():
        os.rename(str(lrc_old), str(lrc_new))

    # DB 업데이트
    track = db.query(Track).filter(Track.file_path == str(p)).first()
    if track:
        track.file_path = str(new_path)
        db.commit()

    # 활동 로그
    from app.core.log_writer import write_activity_log
    write_activity_log(db, "rename",
                       f"파일명 변경: {p.name} → {new_path.name}",
                       action="rename",
                       file_path=str(new_path),
                       username=getattr(current_user, "username", None))

    return {"ok": True, "new_path": str(new_path), "new_name": new_path.name}


# ── 파일 내장 커버 목록 ─────────────────────────────────────
@router.get("/covers")
def get_covers(
    path: str = Query(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """오디오 파일에 내장된 모든 커버아트 목록 반환."""
    p = _validate_path(path, db, allow_workspace=True)
    if not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    cached = _cache.get_covers(str(p))
    if cached is not None:
        return cached

    from urllib.parse import quote as urlquote
    covers = list_covers(str(p))
    for c in covers:
        c["url"] = f"/api/browse/file-cover?path={urlquote(str(p))}&index={c['index']}"
    _cache.set_covers(str(p), covers)
    return covers


# ── 파일 내장 커버 서빙 ─────────────────────────────────────
@router.get("/file-cover")
def get_file_cover(
    request: Request,
    path: str = Query(...),
    index: int = Query(0),
    db: Session = Depends(get_db),
):
    """오디오 파일의 내장 커버아트를 이미지로 반환."""
    # 서버 사이드 커버 데이터 캐시 확인 (DB 쿼리 없이 즉시 반환 — 동시 요청 DB 풀 고갈 방지)
    cache_key = f"{path}:{index}"
    cached = _cache.get_cover_data(cache_key)
    if cached:
        data, mime, etag = cached
        if_none_match = request.headers.get("if-none-match")
        if etag and if_none_match == etag:
            return Response(status_code=304, headers={
                "ETag": etag,
                "Cache-Control": "private, max-age=3600",
            })
        headers = {"Cache-Control": "private, max-age=3600"}
        if etag:
            headers["ETag"] = etag
        return Response(content=data, media_type=mime, headers=headers)

    # 캐시 미스: 경로 검증 + 파일에서 커버 추출
    p = _validate_path(path, db, allow_workspace=True)
    if not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # ETag: 파일 mtime 기반
    try:
        mtime = p.stat().st_mtime
        etag = f'"{int(mtime)}-{index}"'
    except OSError:
        etag = None

    if_none_match = request.headers.get("if-none-match")
    if etag and if_none_match == etag:
        return Response(status_code=304, headers={
            "ETag": etag,
            "Cache-Control": "private, max-age=3600",
        })

    result = extract_cover_at(str(p), index) if index > 0 else extract_cover(str(p))
    if not result:
        raise HTTPException(status_code=404, detail="No cover art in file")

    data, mime = result
    # 서버 캐시에 저장 (이후 동일 요청은 DB 쿼리 없이 처리)
    _cache.set_cover_data(cache_key, (data, mime, etag))

    headers = {"Cache-Control": "private, max-age=3600"}
    if etag:
        headers["ETag"] = etag
    return Response(content=data, media_type=mime, headers=headers)


# ── 이미지 / HTML 등 기타 파일 서빙 ────────────────────────
@router.get("/extra-file")
def get_extra_file(
    path: str = Query(...),
    db: Session = Depends(get_db),
):
    """이미지·HTML 등 폴더 내 기타 파일을 서빙."""
    p = _validate_path(path, db, allow_workspace=True)
    if not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    suffix = p.suffix.lower()
    if suffix in IMAGE_EXTS:
        import mimetypes
        mime = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        data = p.read_bytes()
        return Response(content=data, media_type=mime, headers={"Cache-Control": "private, max-age=3600"})
    elif suffix == ".html":
        data = p.read_bytes()
        return Response(content=data, media_type="text/html; charset=utf-8")
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")


# ── 커버아트 업로드 (파일에 임베드) ────────────────────────
@router.post("/cover-upload")
async def upload_cover(
    path: str = Query(...),
    cover_type: int = Query(3),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """이미지 파일을 오디오 파일에 커버아트로 임베드. cover_type: APIC 타입 (기본 3=Front Cover)."""
    p = _validate_path(path, db, allow_workspace=True)
    if not p.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    content_type = file.content_type or "image/jpeg"
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=422, detail="Image file required")

    image_bytes = await file.read()
    # 같은 타입의 커버만 교체 (write_cover 내부에서 처리)
    ok = write_cover(str(p), image_bytes, content_type, cover_type)
    if not ok:
        raise HTTPException(status_code=500, detail="커버 쓰기 실패 — 로그를 확인하세요")

    # DB 업데이트: has_cover + modified_time 갱신
    track = db.query(Track).filter(Track.file_path == str(p)).first()
    if track:
        track.has_cover = True
        try:
            track.modified_time = p.stat().st_mtime
        except OSError:
            pass
        db.commit()

    # 오디오 폴더에 cover.jpg 저장 (기존 cover 파일 삭제 후)
    ext_img = "png" if "png" in content_type else "jpg"
    for old_name in ("cover.jpg", "cover.png", "folder.jpg", "folder.png",
                     "front.jpg", "front.png", "back.jpg", "back.png"):
        try:
            old_f = p.parent / old_name
            if old_f.exists():
                old_f.unlink()
        except Exception:
            pass
    try:
        (p.parent / f"cover.{ext_img}").write_bytes(image_bytes)
    except Exception:
        pass

    _cache.invalidate_for_file(str(p))
    return {"ok": True}


# ── 폴더 이미지 목록 ────────────────────────────────────────
@router.get("/folder-images")
def get_folder_images(
    path: str = Query(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """폴더 내 이미지 파일 목록 반환."""
    from urllib.parse import quote as urlquote
    p = _validate_path(path, db, allow_workspace=True)
    # 파일이면 부모 폴더로
    folder = p.parent if p.is_file() else p
    if not folder.is_dir():
        raise HTTPException(status_code=404, detail="Folder not found")

    images = []
    try:
        for item in sorted(folder.iterdir()):
            if item.is_file() and item.suffix.lower() in IMAGE_EXTS:
                images.append({
                    "name": item.name,
                    "path": str(item),
                    "url": f"/api/browse/folder-image?path={urlquote(str(item))}",
                    "size": item.stat().st_size,
                })
    except PermissionError:
        pass
    return images


@router.get("/folder-image")
def serve_folder_image(
    path: str = Query(...),
    db: Session = Depends(get_db),
):
    """폴더 내 이미지 파일을 직접 서빙."""
    p = _validate_path(path, db, allow_workspace=True)
    if not p.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    ext = p.suffix.lower()
    if ext not in IMAGE_EXTS:
        raise HTTPException(status_code=400, detail="Not an image file")
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif",  ".webp": "image/webp", ".bmp": "image/bmp",
        ".tiff": "image/tiff", ".tif": "image/tiff",
    }
    return FileResponse(str(p), media_type=mime_map.get(ext, "image/jpeg"), headers={
        "Cache-Control": "public, max-age=3600",
    })


@router.get("/open-file")
def open_file(
    path: str = Query(...),
    db: Session = Depends(get_db),
):
    """폴더 내 HTML 파일을 브라우저에서 직접 열기 (인증 불필요 — 경로는 등록 폴더 하위로 제한)."""
    p = _validate_path(path, db, allow_workspace=True)
    if not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if p.suffix.lower() != ".html":
        raise HTTPException(status_code=400, detail="Not an HTML file")
    return FileResponse(str(p), media_type="text/html; charset=utf-8")


class CoverFromFolderBody(BaseModel):
    image_path: str
    audio_paths: list[str]
    cover_type: int = 3


@router.post("/cover-from-folder")
def apply_cover_from_folder(
    body: CoverFromFolderBody,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """폴더 내 이미지 파일을 오디오 파일들에 커버아트로 임베드. cover_type: APIC 타입 (기본 3=Front Cover)."""
    img_p = _validate_path(body.image_path, db, allow_workspace=True)
    if not img_p.is_file() or img_p.suffix.lower() not in IMAGE_EXTS:
        raise HTTPException(status_code=400, detail="Invalid image path")

    ext = img_p.suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp"}
    content_type = mime_map.get(ext, "image/jpeg")
    image_bytes = img_p.read_bytes()

    results = []
    for audio_path in body.audio_paths:
        try:
            ap = _validate_path(audio_path, db, allow_workspace=True)
            # 같은 타입의 커버만 교체 (write_cover 내부에서 처리)
            ok = write_cover(str(ap), image_bytes, content_type, body.cover_type)
            if ok:
                track = db.query(Track).filter(Track.file_path == str(ap)).first()
                if track:
                    track.has_cover = True
                _cache.invalidate_for_file(str(ap))
                results.append({"path": audio_path, "ok": True})
            else:
                results.append({"path": audio_path, "ok": False, "error": "write_cover failed"})
        except Exception as e:
            results.append({"path": audio_path, "ok": False, "error": str(e)})

    db.commit()
    return {"ok": True, "results": results}


class ExtractCoversBody(BaseModel):
    path: str
    overwrite: bool = False


@router.post("/extract-covers")
def extract_covers_to_folder(
    body: ExtractCoversBody,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """오디오 파일의 커버아트를 같은 폴더에 이미지 파일로 추출."""
    TYPE_NAME_MAP = {
        3: "cover", 4: "back", 0: "other", 1: "icon",
        5: "leaflet", 6: "media", 7: "artist", 8: "artist",
        9: "conductor", 10: "band", 11: "composer", 12: "lyricist",
        13: "location", 14: "during_recording", 15: "during_performance",
        16: "video", 17: "illustration", 18: "band_logo", 19: "publisher_logo",
    }
    MIME_EXT = {
        "image/jpeg": ".jpg", "image/png": ".png",
        "image/gif": ".gif", "image/webp": ".webp",
        "image/bmp": ".bmp", "image/tiff": ".tiff",
    }

    p = _validate_path(body.path, db, allow_workspace=True)
    if not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    covers = list_covers(str(p))
    if not covers:
        raise HTTPException(status_code=404, detail="No cover art found in file")

    folder = p.parent
    saved = []

    for cover_info in covers:
        result = extract_cover_at(str(p), cover_info["index"])
        if not result:
            continue
        data, mime = result
        ext = MIME_EXT.get(mime, ".jpg")

        stem = "cover" if len(covers) == 1 else TYPE_NAME_MAP.get(cover_info["type_id"], f"cover_{cover_info['index']}")
        out_path = folder / (stem + ext)

        if out_path.exists() and not body.overwrite:
            i = 2
            while out_path.exists():
                out_path = folder / f"{stem}_{i}{ext}"
                i += 1

        out_path.write_bytes(data)
        saved.append({"filename": out_path.name, "path": str(out_path), "size_bytes": len(data)})

    if not saved:
        raise HTTPException(status_code=500, detail="Failed to extract any covers")

    return {"ok": True, "saved": saved}


class RemoveCoverBody(BaseModel):
    paths: list[str]


@router.post("/cover-remove")
def remove_cover_endpoint(
    body: RemoveCoverBody,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """오디오 파일들에서 모든 커버아트를 제거."""
    import logging as _logging
    _log = _logging.getLogger(__name__)
    results = []
    for path in body.paths:
        try:
            p = _validate_path(path, db, allow_workspace=True)
            ok = remove_cover(str(p))
            if not ok:
                _log.error(f"[cover-remove] remove_cover returned False for {str(p)}")
                results.append({"path": path, "ok": False, "error": "커버 제거 실패 (파일 쓰기 오류)"})
                continue

            # 제거 후 실제 파일에서 커버가 없어졌는지 검증
            from app.core.tag_reader import read_tags as _read_tags
            verify = _read_tags(str(p))
            if verify.get("has_cover"):
                _log.error(f"[cover-remove] verification failed — cover still present: {str(p)}")
                results.append({"path": path, "ok": False, "error": "제거 후에도 커버가 남아 있습니다"})
                continue

            track = db.query(Track).filter(Track.file_path == str(p)).first()
            if track:
                track.has_cover = False
                try:
                    track.modified_time = p.stat().st_mtime
                except OSError:
                    pass
            else:
                _log.warning(f"[cover-remove] track not found in DB for path: {str(p)}")
            _cache.invalidate_for_file(str(p))
            results.append({"path": path, "ok": True})
        except Exception as e:
            results.append({"path": path, "ok": False, "error": str(e)})
    db.commit()
    return {"ok": True, "results": results}


# ── 오디오 스트리밍 ─────────────────────────────────────
AUDIO_MIME = {
    "mp3": "audio/mpeg", "flac": "audio/flac",
    "m4a": "audio/mp4",  "aac": "audio/aac",
    "ogg": "audio/ogg",  "wav": "audio/wav",
}

@router.get("/stream")
def stream_audio(
    path: str = Query(...),
    db: Session = Depends(get_db),
):
    """오디오 파일을 스트리밍으로 제공 (인증 불필요)."""
    p = _validate_path(path, db, allow_workspace=True)
    if not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    ext = p.suffix.lower().lstrip(".")
    media_type = AUDIO_MIME.get(ext, "application/octet-stream")
    return FileResponse(str(p), media_type=media_type, headers={
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-cache",
    })


# ── LRC 사이드카 파일 읽기 ───────────────────────────────────
@router.get("/lrc-content")
def get_lrc_content(
    path: str = Query(...),
    db: Session = Depends(get_db),
):
    """.lrc 사이드카 파일 또는 내장 가사를 텍스트로 반환."""
    p = _validate_path(path, db, allow_workspace=True)
    if not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # 1) .lrc 사이드카 파일 우선
    lrc_path = p.with_suffix(".lrc")
    if lrc_path.exists():
        try:
            content = lrc_path.read_text(encoding="utf-8", errors="replace")
            return {"source": "lrc_file", "content": content}
        except Exception:
            pass

    # 2) 파일 내장 가사 (DB 또는 태그 직접 읽기)
    track = db.query(Track).filter(Track.file_path == str(p)).first()
    if track and track.lyrics:
        return {"source": "embedded", "content": track.lyrics}

    from app.core.tag_reader import read_tags
    tags = read_tags(str(p))
    if tags.get("lyrics"):
        return {"source": "embedded", "content": tags["lyrics"]}

    raise HTTPException(status_code=404, detail="No lyrics found")


# ── LRC 가사 가져오기 ───────────────────────────────────────
class LrcFileInfo(BaseModel):
    path: str
    title: str = ""
    artist: str = ""
    album: str = ""


class FetchLyricsRequest(BaseModel):
    paths: list[str] = []              # 하위 호환용 (태그 없이 경로만)
    files: list[LrcFileInfo] = []      # 태그 포함 파일 목록
    source: str = "bugs"              # "bugs" | "lrclib" | "auto"
    fallback_source: str = "none"     # "bugs" | "lrclib" | "none"


def _do_fetch_lrc(source: str, file_path, artist: str, title: str, album: str) -> dict:
    """단일 소스로 LRC 검색 수행."""
    if source == "lrclib":
        from app.core.metadata.lrclib import fetch_lrc_for_file
        return fetch_lrc_for_file(str(file_path), artist, title, album)
    else:
        from app.core.metadata.bugs_lyrics import fetch_lrc_for_file
        return fetch_lrc_for_file(str(file_path), artist, title)


@router.post("/fetch-lyrics")
def fetch_lyrics_endpoint(
    req: FetchLyricsRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """LRC 싱크 가사를 가져와 오디오 파일과 같은 폴더에 {파일명}.lrc로 저장.
    source: 'bugs' | 'lrclib' | 'auto' (설정에서 기본/보조 소스 자동 적용)
    fallback_source: 기본 소스 실패 시 시도할 소스 ('bugs' | 'lrclib' | 'none')
    """
    from app.core.config_store import get_config

    # auto 모드: 설정에서 소스 자동 결정
    primary = req.source
    fallback = req.fallback_source
    if req.source == "auto":
        primary = get_config(db, "lrc_primary_source") or "bugs"
        fallback = get_config(db, "lrc_fallback_source") or "none"

    SUPPORTED = {".mp3", ".flac", ".m4a", ".aac", ".ogg"}
    results = []

    # files 우선; 없으면 paths로 폴백 (태그 없는 하위 호환)
    file_list: list[LrcFileInfo] = list(req.files)
    if not file_list:
        file_list = [LrcFileInfo(path=p) for p in req.paths]

    for file_info in file_list:
        path_str = file_info.path
        try:
            p = _validate_path(path_str, db, allow_workspace=True)
            if not p.is_file():
                results.append({"path": path_str, "status": "error", "message": "파일이 아닙니다"})
                continue
            if p.suffix.lower() not in SUPPORTED:
                results.append({"path": path_str, "status": "error", "message": "지원하지 않는 형식입니다"})
                continue

            # 프론트엔드에서 태그 정보를 전달한 경우 우선 사용
            if file_info.title:
                artist = file_info.artist.strip()
                title = file_info.title.strip()
                album = file_info.album.strip()
            else:
                tags = read_tags(str(p))
                artist = (tags.get("artist") or tags.get("album_artist") or "").strip()
                title = (tags.get("title") or p.stem).strip()
                album = (tags.get("album") or "").strip()

            if not title:
                results.append({"path": path_str, "status": "error", "message": "제목 태그가 없습니다"})
                continue

            # 반주/경음악 제목이면 LRC 검색 건너뜀
            if _is_instrumental(title):
                results.append({"path": path_str, "status": "not_found", "message": "반주/경음악 건너뜀"})
                continue

            # 기본 소스로 검색
            result = _do_fetch_lrc(primary, p, artist, title, album)
            source_used = primary

            # 기본 소스 실패 시 보조 소스로 재시도
            if result["status"] in ("not_found", "no_sync") and fallback not in ("none", primary):
                fallback_result = _do_fetch_lrc(fallback, p, artist, title, album)
                if fallback_result["status"] == "ok":
                    result = fallback_result
                    source_used = fallback

            results.append({"path": path_str, "source_used": source_used, **result})

        except HTTPException:
            results.append({"path": path_str, "status": "error", "message": "허용되지 않는 경로입니다"})
        except Exception as e:
            _log.error(f"[fetch-lyrics] error for {path_str}: {e}")
            results.append({"path": path_str, "status": "error", "message": str(e)})

    saved_count = sum(1 for r in results if r.get("status") == "ok")
    notfound_count = sum(1 for r in results if r.get("status") == "not_found")
    error_count = sum(1 for r in results if r.get("status") == "error")
    source_label = f"{primary}" + (f"→{fallback}" if fallback != "none" else "")

    # 활동 로그
    from app.core.log_writer import write_activity_log
    write_activity_log(db, "lrc_search",
                       f"LRC 가사 검색 ({source_label}): {saved_count}개 저장, {notfound_count}개 미발견, {error_count}개 오류",
                       action=f"fetch_lyrics_{primary}",
                       file_path=req.paths[0] if req.paths else None,
                       username=getattr(current_user, "username", None),
                       detail=f"total={len(req.paths)}, saved={saved_count}, not_found={notfound_count}, error={error_count}, fallback={fallback}")

    return {"results": results}


# ── Get LRC 하위 폴더 목록 ────────────────────────────────────
@router.get("/lrc-subfolders")
def get_lrc_subfolders(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """lrc_base_folder 설정의 하위 디렉터리 목록 반환."""
    from app.core.config_store import get_config
    base = get_config(db, "lrc_base_folder") or ""
    if not base:
        raise HTTPException(status_code=400, detail="LRC base folder not configured")
    p = Path(base).resolve()
    if not p.is_dir():
        raise HTTPException(status_code=404, detail="LRC base folder not found")
    children = []
    try:
        for item in sorted(p.iterdir()):
            if not item.is_dir() or item.name.startswith("."):
                continue
            children.append({"name": item.name, "path": str(item)})
    except PermissionError:
        pass
    return {"base": str(p), "folders": children}


# ── 라이브러리 폴더 오디오 파일 스캔 ─────────────────────────
@router.get("/library-audio-files")
def get_library_audio_files(
    folder: str = Query(...),
    recursive: bool = Query(True),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """이동할 폴더 하위 오디오 파일 목록 + LRC 상태 반환."""
    from app.core.config_store import get_destination_folders

    from app.core.config_store import get_config as _get_config
    p = Path(folder).resolve()
    dest_paths = [Path(d["path"]).resolve() for d in get_destination_folders(db)]
    lrc_base = _get_config(db, "lrc_base_folder") or ""
    if lrc_base:
        dest_paths.append(Path(lrc_base).resolve())
    allowed = any(
        p == dest or _is_under_root(p, dest)
        for dest in dest_paths
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Path not in destination folders")
    if not p.is_dir():
        raise HTTPException(status_code=404, detail="Folder not found")

    iterator = p.rglob("*") if recursive else p.iterdir()
    files = []
    for item in sorted(iterator):
        if item.is_file() and item.suffix.lower() in AUDIO_EXTS:
            has_lrc = item.with_suffix(".lrc").exists()
            files.append({"path": str(item), "name": item.name, "has_lrc": has_lrc})

    total = len(files)
    has_lrc_count = sum(1 for f in files if f["has_lrc"])
    return {
        "folder": str(p),
        "total": total,
        "has_lrc": has_lrc_count,
        "missing_lrc": total - has_lrc_count,
        "files": files,
    }


# ── 라이브러리 폴더 LRC 가져오기 ─────────────────────────────
class LibraryFetchLyricsRequest(BaseModel):
    paths: list[str]
    source: str = "bugs"  # "bugs" | "lrclib"


@router.post("/library-fetch-lyrics")
def library_fetch_lyrics(
    req: LibraryFetchLyricsRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """이동할 폴더 파일에 대한 LRC 검색 (이동할 폴더 경로 허용)."""
    if req.source == "lrclib":
        from app.core.metadata.lrclib import fetch_lrc_for_file
    else:
        from app.core.metadata.bugs_lyrics import fetch_lrc_for_file

    results = []
    for path_str in req.paths:
        try:
            p = _validate_path(path_str, db, allow_destinations=True, allow_lrc_folder=True)
            if not p.is_file():
                results.append({"path": path_str, "status": "error", "message": "파일이 아닙니다"})
                continue
            if p.suffix.lower() not in AUDIO_EXTS:
                results.append({"path": path_str, "status": "error", "message": "지원하지 않는 형식입니다"})
                continue
            tags = read_tags(str(p))
            artist = (tags.get("artist") or tags.get("album_artist") or "").strip()
            title = (tags.get("title") or p.stem).strip()
            album = (tags.get("album") or "").strip()
            if not artist or not title:
                results.append({"path": path_str, "status": "error", "message": "아티스트 또는 제목 태그가 없습니다"})
                continue
            if _is_instrumental(title):
                results.append({"path": path_str, "status": "not_found", "message": "반주/경음악 건너뜀"})
                continue
            if req.source == "lrclib":
                result = fetch_lrc_for_file(str(p), artist, title, album)
            else:
                result = fetch_lrc_for_file(str(p), artist, title)
            results.append({"path": path_str, **result})
        except HTTPException:
            results.append({"path": path_str, "status": "error", "message": "허용되지 않는 경로입니다"})
        except Exception as e:
            results.append({"path": path_str, "status": "error", "message": str(e)})

    saved_count = sum(1 for r in results if r.get("status") == "ok")
    notfound_count = sum(1 for r in results if r.get("status") == "not_found")
    error_count = sum(1 for r in results if r.get("status") == "error")

    from app.core.log_writer import write_activity_log
    write_activity_log(db, "lrc_search",
                       f"라이브러리 LRC 검색 ({req.source}): {saved_count}개 저장, {notfound_count}개 미발견, {error_count}개 오류",
                       action=f"library_fetch_lyrics_{req.source}",
                       file_path=req.paths[0] if req.paths else None,
                       username=getattr(current_user, "username", None),
                       detail=f"total={len(req.paths)}, saved={saved_count}, not_found={notfound_count}, error={error_count}")

    return {"results": results}


# ── 태그 기반 파일명 변경 ───────────────────────────────────

class RenameByTagsRequest(BaseModel):
    paths: list[str]
    pattern: str


def _get_file_fields(path: Path, db: Session) -> dict:
    """파일의 태그 필드 dict 반환. DB 우선, 없으면 파일 직접 읽기."""
    track = db.query(Track).filter(Track.file_path == str(path)).first()
    if track:
        return {
            "title": track.title,
            "artist": track.artist,
            "album_artist": track.album_artist,
            "album_title": track.album_title,
            "track_no": track.track_no,
            "total_tracks": track.total_tracks,
            "disc_no": track.disc_no,
            "year": track.year,
            "genre": track.genre,
            "label": track.label,
            "_filename": path.stem,
            "_ext": path.suffix.lstrip("."),
            "_bitrate": track.bitrate,
            "_codec": (track.file_format or "").upper(),
        }
    # DB에 없으면 직접 읽기
    tags = read_tags(str(path))
    return {
        "title": tags.get("title"),
        "artist": tags.get("artist"),
        "album_artist": tags.get("album_artist"),
        "album_title": tags.get("album"),
        "track_no": tags.get("track_no"),
        "total_tracks": tags.get("total_tracks"),
        "disc_no": tags.get("disc_no"),
        "year": tags.get("year"),
        "genre": tags.get("genre"),
        "label": tags.get("label"),
        "_filename": path.stem,
        "_ext": path.suffix.lstrip("."),
        "_bitrate": tags.get("bitrate"),
        "_codec": path.suffix.lstrip(".").upper(),
    }


@router.post("/rename-by-tags/preview")
def rename_by_tags_preview(
    req: RenameByTagsRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """패턴 미리보기 — 파일 시스템 변경 없음."""
    from app.core.pattern_rename import build_new_name

    results = []
    for path_str in req.paths:
        try:
            p = _validate_path(path_str, db, allow_workspace=True)
            if not p.is_file():
                results.append({"path": path_str, "old_name": p.name, "new_name": None, "conflict": False, "error": "파일이 아닙니다"})
                continue

            fields = _get_file_fields(p, db)
            new_name = build_new_name(req.pattern, fields, p.suffix)
            new_path = p.parent / new_name
            conflict = new_path.exists() and new_path != p

            results.append({
                "path": path_str,
                "old_name": p.name,
                "new_name": new_name,
                "conflict": conflict,
                "error": None,
            })
        except HTTPException:
            results.append({"path": path_str, "old_name": Path(path_str).name, "new_name": None, "conflict": False, "error": "허용되지 않는 경로"})
        except Exception as e:
            results.append({"path": path_str, "old_name": Path(path_str).name, "new_name": None, "conflict": False, "error": str(e)})

    return {"results": results}


@router.post("/rename-by-tags")
def rename_by_tags(
    req: RenameByTagsRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """태그 기반 파일명 일괄 변경."""
    from app.core.pattern_rename import build_new_name

    results = []
    success = 0
    failed = 0

    for path_str in req.paths:
        try:
            p = _validate_path(path_str, db, allow_workspace=True)
            if not p.is_file():
                results.append({"path": path_str, "new_path": None, "ok": False, "error": "파일이 아닙니다"})
                failed += 1
                continue

            fields = _get_file_fields(p, db)
            new_name = build_new_name(req.pattern, fields, p.suffix)
            new_path = p.parent / new_name

            # 동일 파일명이면 건너뜀
            if new_path == p:
                results.append({"path": path_str, "new_path": str(new_path), "ok": True, "error": None})
                success += 1
                continue

            # 충돌 감지
            if new_path.exists():
                results.append({"path": path_str, "new_path": None, "ok": False, "error": "conflict"})
                failed += 1
                continue

            # 파일명 변경
            p.rename(new_path)

            # LRC 파일도 동일하게 변경
            lrc_old = p.with_suffix(".lrc")
            lrc_new = new_path.with_suffix(".lrc")
            if lrc_old.exists() and not lrc_new.exists():
                lrc_old.rename(lrc_new)

            # DB 경로 업데이트
            track = db.query(Track).filter(Track.file_path == str(p)).first()
            if track:
                track.file_path = str(new_path)

            # 워크스페이스 아이템 경로 업데이트
            from app.models.workspace import WorkspaceItem
            for wi in db.query(WorkspaceItem).filter(WorkspaceItem.file_path == str(p)).all():
                wi.file_path = str(new_path)

            db.commit()

            # 캐시 무효화
            _cache.invalidate_files(str(p.parent))

            results.append({"path": path_str, "new_path": str(new_path), "ok": True, "error": None})
            success += 1

        except HTTPException:
            results.append({"path": path_str, "new_path": None, "ok": False, "error": "허용되지 않는 경로"})
            failed += 1
        except Exception as e:
            _log.error(f"[rename-by-tags] error for {path_str}: {e}")
            results.append({"path": path_str, "new_path": None, "ok": False, "error": str(e)})
            failed += 1

    # 활동 로그
    from app.core.log_writer import write_activity_log
    write_activity_log(db, "rename",
                       f"태그 기반 파일명 변경: {success}개 성공, {failed}개 실패 (패턴: {req.pattern})",
                       action="rename_by_tags",
                       file_path=req.paths[0] if req.paths else None,
                       username=getattr(current_user, "username", None),
                       detail=f"pattern={req.pattern}, total={len(req.paths)}, success={success}, failed={failed}")

    return {"ok": failed == 0, "results": results, "success": success, "failed": failed}


# ── 이동 대상 폴더 탐색 ─────────────────────────────────────

def _is_under_destination(p: Path, destinations: list) -> bool:
    """경로가 등록된 대상 폴더 하위인지 확인."""
    for dest in destinations:
        dest_p = Path(dest["path"]).resolve()
        try:
            p.relative_to(dest_p)
            return True
        except ValueError:
            continue
    return False


def _get_library_path() -> Path:
    """라이브러리 작업 폴더 경로 반환. 환경변수 LIBRARY_PATH 또는 기본값 /app/data/library."""
    import os
    return Path(os.environ.get("LIBRARY_PATH", "/app/data/library")).resolve()


@router.get("/dest-children")
def get_dest_children(
    path: str = Query(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """등록된 대상 폴더 하위 디렉터리 목록 (대상 폴더 루트 자체 포함)."""
    destinations = get_destination_folders(db)
    if not destinations:
        raise HTTPException(status_code=404, detail="No destination folders registered")

    p = Path(path).resolve()

    # path가 등록된 대상 폴더 루트이거나 그 하위인지 확인
    allowed = False
    for dest in destinations:
        dest_p = Path(dest["path"]).resolve()
        if p == dest_p or _is_under_destination(p, destinations):
            allowed = True
            break

    if not allowed:
        raise HTTPException(status_code=403, detail="Path not under any registered destination folder")

    if not p.is_dir():
        raise HTTPException(status_code=400, detail="Not a directory")

    children = []
    try:
        for item in sorted(p.iterdir()):
            if not item.is_dir() or item.name.startswith("."):
                continue
            has_children = False
            try:
                sub_items = list(item.iterdir())
                has_children = any(x.is_dir() and not x.name.startswith(".") for x in sub_items)
            except PermissionError:
                pass
            children.append({
                "name": item.name,
                "path": str(item),
                "has_children": has_children,
            })
    except PermissionError:
        pass

    return children


class DestMkdirBody(BaseModel):
    parent_path: str
    name: str


@router.post("/dest-mkdir")
def dest_mkdir(
    body: DestMkdirBody,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """대상 폴더 하위에 새 폴더 생성."""
    destinations = get_destination_folders(db)
    parent = Path(body.parent_path).resolve()

    if not _is_under_destination(parent, destinations) and not any(
        Path(d["path"]).resolve() == parent for d in destinations
    ):
        raise HTTPException(status_code=403, detail="Parent not under any registered destination folder")

    name = body.name.strip()
    if not name or "/" in name or "\\" in name or name.startswith("."):
        raise HTTPException(status_code=422, detail="Invalid folder name")

    new_dir = parent / name
    if new_dir.exists():
        raise HTTPException(status_code=409, detail="Folder already exists")

    try:
        new_dir.mkdir(parents=False)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to create directory: {e}")

    return {"ok": True, "path": str(new_dir), "name": new_dir.name}


class MoveFolderBody(BaseModel):
    source_path: str
    dest_path: str


@router.post("/move-folder")
def move_folder(
    body: MoveFolderBody,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """작업 폴더의 하위 폴더를 대상 폴더로 이동 후 DB 경로 업데이트."""
    library_path = _get_library_path()
    destinations = get_destination_folders(db)

    source = Path(body.source_path).resolve()
    dest_parent = Path(body.dest_path).resolve()

    # 소스 검증: library 하위여야 함
    try:
        source.relative_to(library_path)
    except ValueError:
        raise HTTPException(status_code=403, detail="Source must be under the library working folder")

    if not source.is_dir():
        raise HTTPException(status_code=400, detail="Source is not a directory")

    # 대상 검증: 등록된 대상 폴더 하위여야 함
    if not _is_under_destination(dest_parent, destinations) and not any(
        Path(d["path"]).resolve() == dest_parent for d in destinations
    ):
        raise HTTPException(status_code=403, detail="Destination not under any registered destination folder")

    if not dest_parent.is_dir():
        raise HTTPException(status_code=400, detail="Destination parent is not a directory")

    # 이름 충돌 검사
    new_path = dest_parent / source.name
    if new_path.exists():
        raise HTTPException(status_code=409, detail=f"Folder '{source.name}' already exists in destination")

    # 소스 폴더 내 모든 파일 경로 수집 (DB 업데이트용)
    old_prefix = str(source)

    # 이동 실행
    try:
        shutil.move(str(source), str(new_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Move failed: {e}")

    new_prefix = str(new_path)

    # DB Track.file_path 일괄 업데이트 (old_prefix → new_prefix)
    tracks = db.query(Track).filter(Track.file_path.like(f"{old_prefix}%")).all()
    updated_count = 0
    for track in tracks:
        if track.file_path.startswith(old_prefix):
            track.file_path = new_prefix + track.file_path[len(old_prefix):]
            updated_count += 1

    if updated_count > 0:
        db.commit()

    # 캐시 무효화
    _cache.invalidate_files(old_prefix)
    _cache.invalidate_children(str(library_path))
    _cache.invalidate_children(str(source.parent))

    return {
        "ok": True,
        "source": str(source),
        "dest": str(new_path),
        "tracks_updated": updated_count,
    }


class MoveToLibraryBody(BaseModel):
    source_path: str   # 워크스페이스 내 폴더
    dest_path: str     # 라이브러리 내 대상 폴더 (이동할 위치)


@router.post("/move-to-library")
def move_to_library(
    body: MoveToLibraryBody,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """워크스페이스 폴더를 라이브러리로 이동."""
    from app.core.config_store import get_workspace_path, get_library_path
    workspace_base = get_workspace_path(db)
    music_base = get_library_path(db)

    source = Path(body.source_path).resolve()
    dest_parent = Path(body.dest_path).resolve()

    # 소스: 워크스페이스 하위여야 함
    try:
        source.relative_to(workspace_base)
    except ValueError:
        raise HTTPException(status_code=403, detail="Source must be under the workspace folder")

    if not source.is_dir():
        raise HTTPException(status_code=400, detail="Source is not a directory")

    # 대상: 라이브러리 하위여야 함
    try:
        dest_parent.relative_to(music_base)
    except ValueError:
        # scan_folder 에 등록된 경로도 허용
        roots = [Path(f.path).resolve() for f in db.query(ScanFolder).all()]
        if not any(_is_under_root(dest_parent, r) or dest_parent == r for r in roots):
            raise HTTPException(status_code=403, detail="Destination must be under the library folder")

    if not dest_parent.is_dir():
        raise HTTPException(status_code=400, detail="Destination parent is not a directory")

    new_path = dest_parent / source.name
    if new_path.exists():
        raise HTTPException(status_code=409, detail=f"Folder '{source.name}' already exists in destination")

    try:
        shutil.move(str(source), str(new_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Move failed: {e}")

    return {
        "ok": True,
        "source": str(source),
        "dest": str(new_path),
    }


# ── 트랙 DB 전용 정보 업데이트 (타이틀곡, YouTube URL) ────────
@router.post("/set-track-info")
def set_track_info(
    data: dict,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """타이틀곡 여부 및 YouTube URL 등 DB 전용 필드를 업데이트."""
    path = data.get("path", "")
    if not path:
        raise HTTPException(status_code=400, detail="path required")

    track = db.query(Track).filter(Track.file_path == path).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    if "is_title_track" in data:
        track.is_title_track = bool(data["is_title_track"])
    if "youtube_url" in data:
        url = (data["youtube_url"] or "").strip()
        track.youtube_url = url if url else None

    db.commit()
    db.refresh(track)
    return {
        "is_title_track": track.is_title_track,
        "youtube_url": track.youtube_url,
    }



# ── YouTube 뮤직비디오 검색 ───────────────────────────────────
@router.get("/search-youtube-mv")
def search_youtube_mv(
    artist: str,
    title: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """YouTube Data API v3로 뮤직비디오 후보를 검색."""
    from app.core.config_store import get_config
    from app.core.youtube_search import search_music_video

    enabled = get_config(db, "youtube_enabled") == "true"
    api_key = get_config(db, "youtube_api_key") or ""
    if not enabled or not api_key:
        raise HTTPException(status_code=422, detail="youtube_not_configured")

    # 반주/경음악 제목이면 YouTube MV 검색 건너뜀
    if _is_instrumental(title):
        return {"results": [], "skipped": True}

    try:
        results = search_music_video(artist, title, api_key)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {"results": results}


# ── 폴더 HTML 내보내기 ──────────────────────────────────────
@router.post("/export-html-save")
def export_folder_html_save(
    data: dict,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """현재 폴더의 오디오 파일 태그정보를 HTML로 만들어 해당 폴더에 저장."""
    from app.core.html_exporter import _cover_to_b64, build_html, track_model_to_dict, _safe_filename
    from app.core.tag_reader import read_tags

    path = data.get("path", "")
    lang = data.get("lang", "ko")
    p = _validate_path(path, db, allow_workspace=True)
    if not p.is_dir():
        raise HTTPException(status_code=400, detail="Not a directory")

    # 오디오 파일 목록
    audio_items = sorted(
        item for item in p.iterdir()
        if item.is_file() and item.suffix.lower() in AUDIO_EXTS
    )
    if not audio_items:
        raise HTTPException(status_code=404, detail="No audio files found in folder")

    str_paths = [str(item) for item in audio_items]

    # DB 조회
    tracks_map = {
        t.file_path: t
        for t in db.query(Track).filter(Track.file_path.in_(str_paths)).all()
    }

    track_dicts = []
    for item in audio_items:
        track = tracks_map.get(str(item))
        if track:
            track_dicts.append(track_model_to_dict(track))
        else:
            # DB 미등록 파일은 직접 read_tags
            try:
                tags = read_tags(str(item))
                track_dicts.append({
                    "title": tags.get("title") or item.stem,
                    "artist": tags.get("artist"),
                    "album_artist": tags.get("album_artist"),
                    "album_title": tags.get("album_title"),
                    "track_no": tags.get("track_no"),
                    "disc_no": tags.get("disc_no"),
                    "year": tags.get("year"),
                    "genre": tags.get("genre"),
                    "label": tags.get("label"),
                    "isrc": tags.get("isrc"),
                    "comment": tags.get("comment"),
                    "release_date": tags.get("release_date"),
                    "duration": tags.get("duration"),
                    "file_path": str(item),
                    "has_lyrics": bool(tags.get("has_lyrics")),
                    "has_cover": bool(tags.get("has_cover")),
                })
            except Exception:
                continue

    if not track_dicts:
        raise HTTPException(status_code=404, detail="No readable audio files")

    # 앨범 메타 (첫 트랙 기준)
    first = track_dicts[0]
    album_title = first.get("album_title") or p.name
    album_artist = first.get("album_artist") or first.get("artist")
    year = first.get("year")
    genre = first.get("genre")
    label = first.get("label")

    # 앨범 description 조회 (DB)
    # 1순위: DB Track의 album_id
    # 2순위: 실제 파일 태그에서 읽은 album_title+artist (태그 적용 후 DB 미반영 대응)
    # 3순위: DB Track의 album_title+artist (구 값 폴백)
    album_description = None
    from app.models.album import Album as AlbumModel

    def _find_desc_by_title(title, artist):
        if not title:
            return None
        q = db.query(AlbumModel).filter(AlbumModel.title == title)
        if artist:
            q = q.filter(AlbumModel.album_artist == artist)
        alb = q.first()
        return alb.description if alb and alb.description else None

    # 1순위: album_id 직접 조회
    for _p in [str(item) for item in audio_items]:
        _t = tracks_map.get(_p)
        if _t and _t.album_id:
            alb = db.query(AlbumModel).filter(AlbumModel.id == _t.album_id).first()
            if alb and alb.description:
                album_description = alb.description
                break

    # 2순위: 실제 파일 태그 기반 조회 (태그가 DB보다 최신인 경우)
    if not album_description and audio_items:
        try:
            actual = read_tags(str(audio_items[0]))
            actual_title = actual.get("album_title") or ""
            actual_artist = actual.get("album_artist") or actual.get("artist") or ""
            album_description = _find_desc_by_title(actual_title, actual_artist)
        except Exception:
            pass

    # 3순위: DB Track의 album_title+artist (폴백)
    if not album_description:
        album_description = _find_desc_by_title(album_title, album_artist)

    # 커버아트
    cover_paths = [t["file_path"] for t in track_dicts if t.get("has_cover")]
    cover_b64 = _cover_to_b64(track_paths=cover_paths[:3])

    # 타이틀곡 & YouTube URL
    title_track = next((t for t in track_dicts if t.get("is_title_track")), None)
    youtube_url = title_track.get("youtube_url") if title_track else None

    html = build_html(
        tracks=track_dicts,
        album_title=album_title,
        album_artist=album_artist,
        year=year,
        genre=genre,
        label=label,
        cover_b64=cover_b64,
        source_path=str(p),
        description=album_description,
        youtube_url=youtube_url,
        lang=lang,
    )

    # 폴더에 파일 저장
    filename = _safe_filename(f"[앨범카드] {album_artist or p.name} - {album_title}") + ".html"
    out_path = p / filename
    try:
        out_path.write_text(html, encoding="utf-8")
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"파일 저장 실패: {e}")

    return {"filename": filename, "path": str(out_path)}


# ── 폴더 이름 변경 ────────────────────────────────────────────
@router.post("/rename-folder")
def rename_folder(
    data: dict,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """폴더 이름 변경."""
    path = data.get("path", "")
    new_name = (data.get("new_name") or "").strip()
    if not new_name or "/" in new_name or "\\" in new_name:
        raise HTTPException(status_code=422, detail="유효하지 않은 폴더명")

    p = _validate_path(path, db, allow_workspace=True)
    if not p.is_dir():
        raise HTTPException(status_code=400, detail="Not a directory")

    new_path = p.parent / new_name
    if new_path.exists():
        raise HTTPException(status_code=409, detail="이미 존재하는 폴더명입니다")

    p.rename(new_path)

    # DB의 file_path 일괄 업데이트 (구 경로 → 신 경로)
    old_prefix = str(p) + "/"
    new_prefix = str(new_path) + "/"
    tracks = db.query(Track).filter(Track.file_path.like(old_prefix + "%")).all()
    for track in tracks:
        track.file_path = new_prefix + track.file_path[len(old_prefix):]
    # ScanFolder 등록 경로도 업데이트
    scan_folders = db.query(ScanFolder).filter(ScanFolder.path.like(str(p) + "%")).all()
    for sf in scan_folders:
        sf.path = str(new_path) + sf.path[len(str(p)):]
    if tracks or scan_folders:
        db.commit()

    _cache.invalidate_files(str(p.parent))
    return {"old_path": str(p), "new_path": str(new_path), "new_name": new_name}


# ── 기타 파일 삭제 (이미지 / HTML) ───────────────────────────
@router.post("/delete-extra-file")
def delete_extra_file(
    data: dict,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """이미지·HTML 등 기타 파일 삭제."""
    path = data.get("path", "")
    p = _validate_path(path, db, allow_workspace=True)
    if not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    suffix = p.suffix.lower()
    allowed = IMAGE_EXTS | {".html"}
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail="오디오 파일은 삭제할 수 없습니다")

    p.unlink()
    _cache.invalidate_files(str(p.parent))
    return {"deleted": str(p)}


# ── 라이브러리 폴더 삭제 ─────────────────────────────────────
@router.post("/delete-folder")
def delete_folder(
    data: dict,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """라이브러리/대상 폴더 삭제 (빈 폴더만 허용)."""
    path = data.get("path", "")
    destinations = get_destination_folders(db)
    p = Path(path).resolve()

    # 루트 대상 폴더 자체는 삭제 불가
    if any(Path(d["path"]).resolve() == p for d in destinations):
        raise HTTPException(status_code=403, detail="루트 라이브러리 폴더는 삭제할 수 없습니다")

    # 등록된 대상 폴더 하위여야 함
    if not _is_under_destination(p, destinations):
        raise HTTPException(status_code=403, detail="폴더가 등록된 라이브러리 경로 외부에 있습니다")

    if not p.is_dir():
        raise HTTPException(status_code=404, detail="폴더가 존재하지 않습니다")

    # 빈 폴더 검사
    if any(p.iterdir()):
        raise HTTPException(status_code=400, detail="빈 폴더만 삭제할 수 있습니다")

    p.rmdir()

    # ScanFolder에서도 제거
    sf = db.query(ScanFolder).filter(ScanFolder.path == str(p)).first()
    if sf:
        db.delete(sf)
        db.commit()

    _cache.invalidate_files(str(p.parent))
    return {"deleted": str(p)}


# ── 재귀 파일 카운트 (폴더열기 확인 용) ───────────────────────
@router.get("/recursive-count")
def recursive_count(
    path: str = Query(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """폴더 + 하위 폴더의 오디오 파일/폴더 수를 반환 (확인 다이얼로그용)."""
    p = _validate_path(path, db, allow_workspace=True)
    if not p.is_dir():
        raise HTTPException(status_code=400, detail="Not a directory")
    excluded = get_excluded_folders(db)

    folder_count = 0
    file_count = 0
    for root, dirs, files in os.walk(str(p)):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in excluded)
        folder_count += len(dirs)
        file_count += sum(1 for f in files if Path(f).suffix.lower() in AUDIO_EXTS)

    return {"folder_count": folder_count, "file_count": file_count}


# ── 재귀 파일 목록 (폴더별 그룹) ────────────────────────────
@router.post("/recursive-files")
def recursive_files(
    data: dict,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """폴더 + 하위 모든 폴더의 오디오 파일을 폴더별로 그룹화하여 반환."""
    path = data.get("path", "")
    p = _validate_path(path, db, allow_workspace=True)
    if not p.is_dir():
        raise HTTPException(status_code=400, detail="Not a directory")
    excluded = get_excluded_folders(db)

    # 1단계: 폴더별 오디오 파일 경로 수집
    group_structure = []
    for root, dirs, files in os.walk(str(p)):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in excluded)
        audio_files = sorted(f for f in files if Path(f).suffix.lower() in AUDIO_EXTS)
        if audio_files:
            rel = os.path.relpath(root, str(p))
            group_structure.append({
                "folder_path": root,
                "folder_name": Path(root).name,
                "relative_path": "" if rel == "." else rel,
                "file_paths": [os.path.join(root, f) for f in audio_files],
            })

    all_paths = [fp for g in group_structure for fp in g["file_paths"]]
    if not all_paths:
        return {"groups": [], "total_files": 0, "total_folders": 0}

    # 2단계: DB 한 번에 조회
    tracks_map = {
        t.file_path: t
        for t in db.query(Track).filter(Track.file_path.in_(all_paths)).all()
    }

    # 3단계: 그룹별 파일 정보 구성 (get_files 엔드포인트와 동일한 형식)
    groups = []
    for g in group_structure:
        folder_path = Path(g["folder_path"])
        try:
            lrc_set = {item.stem for item in folder_path.iterdir()
                       if item.is_file() and item.suffix.lower() == ".lrc"}
        except Exception:
            lrc_set = set()

        file_entries = []
        for fp in g["file_paths"]:
            item = Path(fp)
            track = tracks_map.get(fp)
            try:
                stat = item.stat()
            except OSError:
                continue
            has_lrc = item.stem in lrc_set
            if track:
                file_entries.append({
                    "id": track.id, "album_id": track.album_id,
                    "filename": item.name, "path": fp,
                    "title": track.title or item.stem,
                    "artist": track.artist, "album_artist": track.album_artist,
                    "album_title": track.album_title,
                    "track_no": track.track_no, "total_tracks": track.total_tracks,
                    "disc_no": track.disc_no, "year": track.year,
                    "release_date": track.release_date, "genre": track.genre,
                    "label": track.label, "isrc": track.isrc,
                    "duration": track.duration, "bitrate": track.bitrate,
                    "sample_rate": track.sample_rate, "tag_version": track.tag_version,
                    "comment": track.comment,
                    "file_format": (track.file_format or "").upper(),
                    "has_cover": track.has_cover, "has_lyrics": track.has_lyrics,
                    "is_title_track": bool(track.is_title_track),
                    "youtube_url": track.youtube_url, "has_lrc": has_lrc,
                    "lyrics": track.lyrics,
                    "file_size": stat.st_size, "modified_time": stat.st_mtime,
                    "scanned": True,
                })
            else:
                file_entries.append({
                    "id": None, "album_id": None,
                    "filename": item.name, "path": fp,
                    "title": item.stem, "artist": None, "album_artist": None,
                    "album_title": None, "track_no": None, "total_tracks": None,
                    "disc_no": None, "year": None, "release_date": None,
                    "genre": None, "label": None, "isrc": None,
                    "duration": None, "bitrate": None, "sample_rate": None,
                    "tag_version": None, "comment": None,
                    "file_format": item.suffix.lstrip(".").upper(),
                    "has_cover": False, "has_lyrics": False,
                    "is_title_track": False, "youtube_url": None,
                    "has_lrc": has_lrc, "lyrics": None,
                    "file_size": stat.st_size, "modified_time": stat.st_mtime,
                    "scanned": False,
                })
        if file_entries:
            groups.append({
                "folder_path": g["folder_path"],
                "folder_name": g["folder_name"],
                "relative_path": g["relative_path"],
                "files": file_entries,
            })

    return {
        "groups": groups,
        "total_files": sum(len(g["files"]) for g in groups),
        "total_folders": len(groups),
    }
