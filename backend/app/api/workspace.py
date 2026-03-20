"""
워크스페이스 API

흐름:
  1. GET  /current-session          현재 editing 세션 조회 (없으면 자동 생성)
  2. POST /load-folder              라이브러리 폴더에서 파일 불러오기
  3. POST /load-files               개별 파일 불러오기
  4. PUT  /items/{id}/stage-tags    태그 변경 임시 저장 (파일 미반영)
  5. PUT  /items/{id}/stage-rename  파일명 변경 임시 저장 (파일 미반영)
  6. POST /session/{id}/apply       전체 스테이징 → 실제 파일에 일괄 반영
  7. POST /items/{id}/apply         단일 파일 즉시 반영
  8. GET  /history                  완료된 세션 히스토리 목록
  9. GET  /history/{session_id}     세션 상세
"""
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.auth import get_current_user
from app.models.workspace import WorkspaceSession, WorkspaceItem, WorkspaceHistoryOp
from app.core.tag_reader import read_tags
from app.core.tag_writer import write_tags

_log = logging.getLogger(__name__)

AUDIO_EXTS = {".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wav", ".wma"}

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


# ── 헬퍼 ──────────────────────────────────────────────────

def _get_or_create_session(db: Session, username: Optional[str] = None) -> WorkspaceSession:
    """현재 editing 상태 세션 반환. 없으면 신규 생성."""
    session = db.query(WorkspaceSession).filter(
        WorkspaceSession.status == "editing"
    ).order_by(WorkspaceSession.id.desc()).first()
    if not session:
        session = WorkspaceSession(status="editing", username=username)
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def _item_to_dict(item: WorkspaceItem) -> dict:
    return {
        "id": item.id,
        "session_id": item.session_id,
        "file_path": item.file_path,
        "filename": Path(item.file_path).name,
        "original_tags": item.original_tags or {},
        "pending_tags": item.pending_tags or {},
        "pending_rename": item.pending_rename,
        "status": item.status,
        "apply_error": item.apply_error,
        "sort_order": item.sort_order,
        "added_at": item.added_at.isoformat() if item.added_at else None,
        "applied_at": item.applied_at.isoformat() if item.applied_at else None,
        "has_changes": bool(item.pending_tags or item.pending_rename),
    }


def _session_to_dict(session: WorkspaceSession, include_items: bool = False) -> dict:
    d = {
        "id": session.id,
        "status": session.status,
        "name": session.name,
        "username": session.username,
        "note": session.note,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "applied_at": session.applied_at.isoformat() if session.applied_at else None,
        "item_count": len(session.items),
        "pending_count": sum(1 for i in session.items if i.pending_tags or i.pending_rename),
    }
    if include_items:
        d["items"] = [_item_to_dict(i) for i in session.items]
    return d


def _validate_library_path(path: str, db: Session) -> Path:
    """라이브러리 마운트 경로 검증 (MUSIC_BASE_PATH 하위 또는 scan_folder)."""
    from app.models.scan_folder import ScanFolder
    p = Path(path).resolve()
    # scan_folder 에 등록된 경로 하위인지 확인
    roots = [Path(f.path).resolve() for f in db.query(ScanFolder).all()]
    # 환경변수 MUSIC_BASE_PATH 도 허용
    music_base = Path(os.getenv("MUSIC_BASE_PATH", "/music")).resolve()
    roots.append(music_base)
    for root in roots:
        try:
            p.relative_to(root)
            return p
        except ValueError:
            continue
    raise HTTPException(status_code=403, detail=f"허용되지 않는 경로입니다: {path}")


# ── 세션 관리 ──────────────────────────────────────────────

@router.get("/current-session")
def get_current_session(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """현재 editing 세션 반환 (없으면 자동 생성)."""
    username = getattr(current_user, "username", None)
    session = _get_or_create_session(db, username)
    return _session_to_dict(session, include_items=True)


@router.post("/session/new")
def new_session(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """새 세션 시작. 기존 editing 세션은 discarded 처리."""
    username = getattr(current_user, "username", None)
    # 기존 editing 세션 버리기
    db.query(WorkspaceSession).filter(
        WorkspaceSession.status == "editing"
    ).update({"status": "discarded"})
    db.commit()
    session = WorkspaceSession(status="editing", username=username)
    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_to_dict(session, include_items=True)


@router.patch("/session/{session_id}")
def update_session(
    session_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """세션 이름/메모 수정."""
    session = db.get(WorkspaceSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    if "name" in body:
        session.name = body["name"]
    if "note" in body:
        session.note = body["note"]
    db.commit()
    return _session_to_dict(session)


@router.post("/session/{session_id}/discard")
def discard_session(
    session_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """세션 폐기 (아이템 삭제 포함)."""
    session = db.get(WorkspaceSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    session.status = "discarded"
    db.commit()
    return {"ok": True}


# ── 파일 불러오기 ──────────────────────────────────────────

class LoadFolderRequest(BaseModel):
    folder_path: str
    recursive: bool = False


@router.post("/load-folder")
def load_folder(
    req: LoadFolderRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """라이브러리 폴더의 오디오 파일들을 현재 세션에 추가."""
    username = getattr(current_user, "username", None)
    p = _validate_library_path(req.folder_path, db)
    if not p.is_dir():
        raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다")

    session = _get_or_create_session(db, username)

    # 이미 세션에 있는 파일 경로 수집
    existing_paths = {i.file_path for i in session.items}

    iterator = p.rglob("*") if req.recursive else p.iterdir()
    audio_files = sorted(
        f for f in iterator
        if f.is_file() and f.suffix.lower() in AUDIO_EXTS
    )

    added = 0
    skipped = 0
    max_order = max((i.sort_order for i in session.items), default=-1)

    for audio in audio_files:
        path_str = str(audio)
        if path_str in existing_paths:
            skipped += 1
            continue
        tags = read_tags(path_str)
        max_order += 1
        item = WorkspaceItem(
            session_id=session.id,
            file_path=path_str,
            original_tags=tags,
            sort_order=max_order,
        )
        db.add(item)
        added += 1

    db.commit()
    db.refresh(session)
    return {
        "ok": True,
        "added": added,
        "skipped": skipped,
        "session": _session_to_dict(session, include_items=True),
    }


class LoadFilesRequest(BaseModel):
    file_paths: list[str]


@router.post("/load-files")
def load_files(
    req: LoadFilesRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """개별 파일들을 현재 세션에 추가."""
    username = getattr(current_user, "username", None)
    session = _get_or_create_session(db, username)
    existing_paths = {i.file_path for i in session.items}
    max_order = max((i.sort_order for i in session.items), default=-1)

    added = 0
    skipped = 0
    errors = []

    for path_str in req.file_paths:
        try:
            p = _validate_library_path(path_str, db)
            if not p.is_file():
                errors.append({"path": path_str, "error": "파일이 아닙니다"})
                continue
            if p.suffix.lower() not in AUDIO_EXTS:
                errors.append({"path": path_str, "error": "지원하지 않는 형식"})
                continue
            if path_str in existing_paths:
                skipped += 1
                continue
            tags = read_tags(path_str)
            max_order += 1
            db.add(WorkspaceItem(
                session_id=session.id,
                file_path=path_str,
                original_tags=tags,
                sort_order=max_order,
            ))
            added += 1
        except HTTPException as e:
            errors.append({"path": path_str, "error": e.detail})

    db.commit()
    db.refresh(session)
    return {
        "ok": True,
        "added": added,
        "skipped": skipped,
        "errors": errors,
        "session": _session_to_dict(session, include_items=True),
    }


# ── 아이템 관리 ────────────────────────────────────────────

@router.get("/items")
def get_items(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """현재 세션의 아이템 목록."""
    session = db.query(WorkspaceSession).filter(
        WorkspaceSession.status == "editing"
    ).order_by(WorkspaceSession.id.desc()).first()
    if not session:
        return {"items": [], "session_id": None}
    return {
        "session_id": session.id,
        "items": [_item_to_dict(i) for i in session.items],
    }


@router.delete("/items/{item_id}")
def remove_item(
    item_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """아이템을 세션에서 제거."""
    item = db.get(WorkspaceItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.delete("/items")
def clear_items(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """현재 세션의 모든 아이템 제거 (세션 유지)."""
    session = db.query(WorkspaceSession).filter(
        WorkspaceSession.status == "editing"
    ).order_by(WorkspaceSession.id.desc()).first()
    if session:
        db.query(WorkspaceItem).filter(WorkspaceItem.session_id == session.id).delete()
        db.commit()
    return {"ok": True}


# ── 스테이징 ────────────────────────────────────────────────

class StageTagsRequest(BaseModel):
    tags: dict


@router.put("/items/{item_id}/stage-tags")
def stage_tags(
    item_id: int,
    req: StageTagsRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """태그 변경을 임시 저장 (파일 미반영)."""
    item = db.get(WorkspaceItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")

    # 기존 pending_tags에 병합
    merged = dict(item.pending_tags or {})
    merged.update(req.tags)
    item.pending_tags = merged

    # 히스토리 기록
    db.add(WorkspaceHistoryOp(
        session_id=item.session_id,
        file_path=item.file_path,
        op_type="tag_edit",
        op_detail={"tags": req.tags},
    ))
    db.commit()
    return _item_to_dict(item)


class StageRenameRequest(BaseModel):
    new_name: str


@router.put("/items/{item_id}/stage-rename")
def stage_rename(
    item_id: int,
    req: StageRenameRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """파일명 변경을 임시 저장 (파일 미반영)."""
    item = db.get(WorkspaceItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")

    item.pending_rename = req.new_name
    db.add(WorkspaceHistoryOp(
        session_id=item.session_id,
        file_path=item.file_path,
        op_type="rename",
        op_detail={"old_name": Path(item.file_path).name, "new_name": req.new_name},
    ))
    db.commit()
    return _item_to_dict(item)


@router.delete("/items/{item_id}/stage-tags")
def unstage_tags(
    item_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """스테이징된 태그 변경 취소 (원본으로 되돌리기)."""
    item = db.get(WorkspaceItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")
    item.pending_tags = None
    item.pending_rename = None
    db.commit()
    return _item_to_dict(item)


@router.get("/items/{item_id}/diff")
def get_item_diff(
    item_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """original_tags vs pending_tags 비교."""
    item = db.get(WorkspaceItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")

    original = item.original_tags or {}
    pending = item.pending_tags or {}
    all_keys = set(original) | set(pending)

    diff = {}
    for k in all_keys:
        ov = original.get(k)
        pv = pending.get(k)
        if ov != pv:
            diff[k] = {"before": ov, "after": pv}

    return {
        "item_id": item_id,
        "file_path": item.file_path,
        "diff": diff,
        "pending_rename": item.pending_rename,
        "original_name": Path(item.file_path).name,
    }


# ── 적용 (Apply) ───────────────────────────────────────────

def _apply_item(item: WorkspaceItem, db: Session) -> dict:
    """단일 아이템의 스테이징 변경을 실제 파일에 반영."""
    errors = []
    applied_ops = []

    # 1. 태그 쓰기
    if item.pending_tags:
        try:
            write_tags(item.file_path, item.pending_tags)
            applied_ops.append("tag_write")
        except Exception as e:
            errors.append(f"태그 쓰기 실패: {e}")

    # 2. 파일명 변경
    if item.pending_rename and not errors:
        try:
            old_path = Path(item.file_path)
            new_path = old_path.parent / item.pending_rename
            if new_path.exists() and new_path != old_path:
                errors.append(f"파일명 충돌: {item.pending_rename}")
            else:
                old_path.rename(new_path)
                item.file_path = str(new_path)
                applied_ops.append("rename")
        except Exception as e:
            errors.append(f"파일명 변경 실패: {e}")

    if errors:
        item.status = "error"
        item.apply_error = "; ".join(errors)
    else:
        item.status = "applied"
        item.apply_error = None
        item.pending_tags = None
        item.pending_rename = None
        item.applied_at = datetime.now(timezone.utc)

    # 히스토리 기록
    db.add(WorkspaceHistoryOp(
        session_id=item.session_id,
        file_path=item.file_path,
        op_type="apply",
        op_detail={"ops": applied_ops, "errors": errors},
    ))
    return {"ok": not errors, "errors": errors, "ops": applied_ops}


@router.post("/items/{item_id}/apply")
def apply_item(
    item_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """단일 파일만 즉시 적용."""
    item = db.get(WorkspaceItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")
    result = _apply_item(item, db)
    db.commit()
    return {**result, "item": _item_to_dict(item)}


@router.post("/session/{session_id}/apply")
def apply_session(
    session_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """세션의 모든 스테이징 변경을 실제 파일에 일괄 반영."""
    session = db.get(WorkspaceSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    pending_items = [
        i for i in session.items
        if i.status == "pending" and (i.pending_tags or i.pending_rename)
    ]

    if not pending_items:
        return {"ok": True, "applied": 0, "errors": 0, "message": "변경 사항이 없습니다"}

    applied_count = 0
    error_count = 0
    results = []

    for item in pending_items:
        r = _apply_item(item, db)
        results.append({"path": item.file_path, **r})
        if r["ok"]:
            applied_count += 1
        else:
            error_count += 1

    # 모두 적용 완료 시 세션 상태 업데이트
    all_done = all(i.status in ("applied", "error", "skipped") for i in session.items)
    if all_done and error_count == 0:
        session.status = "applied"
        session.applied_at = datetime.now(timezone.utc)

    db.commit()
    return {
        "ok": error_count == 0,
        "applied": applied_count,
        "errors": error_count,
        "results": results,
        "session_status": session.status,
    }


# ── 히스토리 ────────────────────────────────────────────────

@router.get("/history")
def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """완료된 세션 히스토리 목록 (editing 제외)."""
    q = db.query(WorkspaceSession).filter(
        WorkspaceSession.status != "editing"
    ).order_by(WorkspaceSession.id.desc())

    total = q.count()
    sessions = q.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "sessions": [_session_to_dict(s) for s in sessions],
    }


@router.get("/history/{session_id}")
def get_history_detail(
    session_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """히스토리 세션 상세 (아이템 + 작업 로그)."""
    session = db.get(WorkspaceSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    ops = db.query(WorkspaceHistoryOp).filter(
        WorkspaceHistoryOp.session_id == session_id
    ).order_by(WorkspaceHistoryOp.created_at).all()

    return {
        **_session_to_dict(session, include_items=True),
        "ops": [
            {
                "id": op.id,
                "file_path": op.file_path,
                "filename": Path(op.file_path).name,
                "op_type": op.op_type,
                "op_detail": op.op_detail,
                "created_at": op.created_at.isoformat() if op.created_at else None,
            }
            for op in ops
        ],
    }


@router.delete("/history/{session_id}")
def delete_history(
    session_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """히스토리 세션 삭제 (아이템, 로그 포함)."""
    session = db.get(WorkspaceSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    if session.status == "editing":
        raise HTTPException(status_code=400, detail="현재 편집 중인 세션은 삭제할 수 없습니다")
    db.delete(session)
    db.commit()
    return {"ok": True}


# ── 라이브러리 탐색 (피커용) ──────────────────────────────────

@router.get("/library/roots")
def library_roots(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """라이브러리 루트 폴더 목록 (피커용)."""
    from app.models.scan_folder import ScanFolder
    folders = db.query(ScanFolder).all()
    music_base = os.getenv("MUSIC_BASE_PATH", "/music")

    roots = []
    seen = set()

    # MUSIC_BASE_PATH 우선
    p = Path(music_base)
    if p.is_dir() and str(p) not in seen:
        seen.add(str(p))
        roots.append({
            "name": p.name or "music",
            "path": str(p),
            "has_children": any(True for _ in p.iterdir() if _.is_dir()),
        })

    for f in folders:
        p = Path(f.path)
        if str(p) not in seen and p.is_dir():
            seen.add(str(p))
            roots.append({
                "name": f.name or p.name,
                "path": str(p),
                "has_children": any(True for _ in p.iterdir() if _.is_dir()),
            })

    return {"roots": roots}


@router.get("/library/children")
def library_children(
    path: str = Query(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """라이브러리 폴더의 하위 목록 (폴더 + 오디오 파일)."""
    p = _validate_library_path(path, db)
    if not p.is_dir():
        raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다")

    items = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    result_dirs = []
    result_files = []

    for item in items:
        if item.name.startswith("."):
            continue
        if item.is_dir():
            has_audio = any(
                f.suffix.lower() in AUDIO_EXTS
                for f in item.rglob("*") if f.is_file()
            )
            result_dirs.append({
                "name": item.name,
                "path": str(item),
                "type": "folder",
                "has_children": any(True for _ in item.iterdir() if _.is_dir()),
                "has_audio": has_audio,
            })
        elif item.is_file() and item.suffix.lower() in AUDIO_EXTS:
            result_files.append({
                "name": item.name,
                "path": str(item),
                "type": "file",
                "ext": item.suffix.lower().lstrip("."),
            })

    return {
        "path": str(p),
        "folders": result_dirs,
        "files": result_files,
    }
