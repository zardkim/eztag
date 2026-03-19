from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

from app.core.backup_manager import (
    create_backup, list_backups, _validate_filename,
    delete_backup, restore_backup,
)

router = APIRouter(prefix="/api/backup", tags=["backup"])

DATABASE_URL = os.environ.get("DATABASE_URL", "")

_backup_status = {"running": False, "last_backup": None, "error": None}


@router.get("/status")
def backup_status():
    return _backup_status


@router.post("/create")
def create_backup_endpoint():
    if _backup_status["running"]:
        raise HTTPException(status_code=409, detail="백업이 이미 진행 중입니다")
    _backup_status["running"] = True
    _backup_status["error"] = None
    try:
        filename = create_backup(DATABASE_URL)
        _backup_status["last_backup"] = filename
        return {"ok": True, "filename": filename}
    except Exception as e:
        _backup_status["error"] = str(e)
        raise HTTPException(status_code=500, detail=f"백업 실패: {e}")
    finally:
        _backup_status["running"] = False


@router.get("/list")
def list_backups_endpoint():
    return {"backups": list_backups()}


@router.get("/download/{filename}")
def download_backup(filename: str):
    try:
        path = _validate_filename(filename)
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    return FileResponse(path=str(path), filename=filename, media_type="application/gzip")


@router.post("/restore/{filename}")
def restore_backup_endpoint(filename: str):
    if _backup_status["running"]:
        raise HTTPException(status_code=409, detail="백업 작업이 진행 중입니다")
    try:
        result = restore_backup(filename, DATABASE_URL)
        return result
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"복원 실패: {e}")


@router.delete("/{filename}")
def delete_backup_endpoint(filename: str):
    try:
        delete_backup(filename)
        return {"ok": True, "deleted": filename}
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
