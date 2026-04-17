from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import os
import shutil
from pathlib import Path

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


@router.post("/upload")
async def upload_backup_endpoint(file: UploadFile = File(...)):
    """백업 파일 업로드 (외부에서 다운받은 .tar.gz 복원용)."""
    original_name = Path(file.filename).name if file.filename else ""
    if not original_name.endswith(".tar.gz") or "/" in original_name or ".." in original_name:
        raise HTTPException(status_code=400, detail="올바른 백업 파일(.tar.gz)이 아닙니다")
    dest_dir = Path(os.environ.get("BACKUP_DIR", "/app/data/backup"))
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / original_name
    try:
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
    finally:
        await file.close()
    return {"ok": True, "filename": original_name}


@router.delete("/{filename}")
def delete_backup_endpoint(filename: str):
    try:
        delete_backup(filename)
        return {"ok": True, "deleted": filename}
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
