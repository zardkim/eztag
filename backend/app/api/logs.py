from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
from typing import Optional
import os

from app.database import get_db
from app.models.scan_log import ScanLog
from app.models.activity_log import ActivityLog
from app.schemas.log import ScanLogOut, ScanLogList, ActivityLogOut, ActivityLogList
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/logs", tags=["logs"])

LOG_DIR = os.environ.get("LOG_DIR", "/app/data/logs")


@router.get("/scan", response_model=ScanLogList)
def list_scan_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(ScanLog).order_by(ScanLog.started_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return ScanLogList(total=total, items=items)


@router.delete("/scan")
def clear_scan_logs(db: Session = Depends(get_db)):
    count = db.query(ScanLog).count()
    db.query(ScanLog).delete()
    db.commit()
    return {"deleted": count}


@router.get("/files")
def list_log_files():
    log_dir = Path(LOG_DIR)
    files = []
    for name in ["app.log", "error.log"]:
        p = log_dir / name
        if p.exists():
            files.append({"name": name, "size": p.stat().st_size})
    return {"files": files}


@router.get("/download/{filename}")
def download_log_file(filename: str):
    if filename not in ("app.log", "error.log"):
        raise HTTPException(status_code=400, detail="Invalid log filename")
    path = Path(LOG_DIR) / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Log file not found")
    return FileResponse(path=str(path), filename=f"eztag_{filename}", media_type="text/plain")


# ── 활동 로그 ──────────────────────────────────────────────

@router.get("/activity", response_model=ActivityLogList)
def list_activity_logs(
    log_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """활동 로그 목록 (타입/검색어/날짜 필터, 최신순)."""
    query = db.query(ActivityLog)

    if log_type:
        query = query.filter(ActivityLog.log_type == log_type)

    if search:
        like = f"%{search}%"
        query = query.filter(
            ActivityLog.message.ilike(like)
            | ActivityLog.file_path.ilike(like)
            | ActivityLog.username.ilike(like)
            | ActivityLog.action.ilike(like)
        )

    if date_from:
        try:
            dt = datetime.fromisoformat(date_from)
            query = query.filter(ActivityLog.created_at >= dt)
        except ValueError:
            pass

    if date_to:
        try:
            dt = datetime.fromisoformat(date_to)
            query = query.filter(ActivityLog.created_at <= dt)
        except ValueError:
            pass

    total = query.count()
    items = query.order_by(ActivityLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ActivityLogList(total=total, items=items)


@router.delete("/activity")
def clear_activity_logs(
    log_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """활동 로그 전체 또는 특정 타입 삭제."""
    query = db.query(ActivityLog)
    if log_type:
        query = query.filter(ActivityLog.log_type == log_type)
    count = query.count()
    query.delete(synchronize_session=False)
    db.commit()
    return {"deleted": count}
