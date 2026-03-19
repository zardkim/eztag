import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.scan_folder import ScanFolder
from app.models.scan_log import ScanLog
from app.schemas.scan import ScanFolderCreate, ScanFolderOut, ScanResult
from app.core.scanner import MusicScanner
import app.core.cache as _cache

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scan", tags=["scan"])

_scan_status = {"running": False, "last_result": None}


@router.get("/folders", response_model=list[ScanFolderOut])
def list_folders(db: Session = Depends(get_db)):
    return db.query(ScanFolder).order_by(ScanFolder.path).all()


@router.post("/folders", response_model=ScanFolderOut)
def add_folder(body: ScanFolderCreate, db: Session = Depends(get_db)):
    existing = db.query(ScanFolder).filter(ScanFolder.path == body.path).first()
    if existing:
        raise HTTPException(status_code=409, detail="Folder already registered")
    folder = ScanFolder(path=body.path, name=body.name)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@router.delete("/folders/{folder_id}")
def remove_folder(folder_id: int, db: Session = Depends(get_db)):
    folder = db.query(ScanFolder).filter(ScanFolder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    db.delete(folder)
    db.commit()
    return {"ok": True}


@router.get("/status")
def scan_status():
    return _scan_status


@router.post("/start", response_model=ScanResult)
def start_scan(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if _scan_status["running"]:
        raise HTTPException(status_code=409, detail="Scan already running")

    scan_log = ScanLog(scan_type="manual", status="running", started_at=datetime.now(timezone.utc))
    db.add(scan_log)
    db.commit()
    db.refresh(scan_log)

    scanner = MusicScanner(db)
    _scan_status["running"] = True
    try:
        result = scanner.scan_all()
        _scan_status["last_result"] = result

        scan_log.status = "partial" if result.get("errors", 0) > 0 else "success"
        scan_log.scanned = result.get("scanned", 0)
        scan_log.added = result.get("added", 0)
        scan_log.updated = result.get("updated", 0)
        scan_log.skipped = result.get("skipped", 0)
        scan_log.errors = result.get("errors", 0)
        scan_log.duration = result.get("duration", 0.0)
        scan_log.finished_at = datetime.now(timezone.utc)
        db.commit()
        _cache.clear_all()
        logger.info(f"Scan complete: {result}")
    except Exception as e:
        scan_log.status = "error"
        scan_log.error_message = str(e)
        scan_log.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.error(f"Scan failed: {e}")
        raise
    finally:
        _scan_status["running"] = False

    return result


@router.post("/cleanup")
def cleanup_missing(db: Session = Depends(get_db)):
    scan_log = ScanLog(scan_type="cleanup", status="running", started_at=datetime.now(timezone.utc))
    db.add(scan_log)
    db.commit()
    db.refresh(scan_log)

    try:
        scanner = MusicScanner(db)
        removed = scanner.cleanup_missing()
        scan_log.status = "success"
        scan_log.scanned = removed
        scan_log.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Cleanup complete: {removed} removed")
        return {"removed": removed}
    except Exception as e:
        scan_log.status = "error"
        scan_log.error_message = str(e)
        scan_log.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.error(f"Cleanup failed: {e}")
        raise
