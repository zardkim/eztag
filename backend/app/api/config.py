from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.core.auth import get_current_user
from app.schemas.config import ConfigResponse, ConfigUpdate, ConfigItem
from app.core.config_store import get_all_config, set_bulk_config, DEFAULTS, get_destination_folders, set_destination_folders

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/", response_model=ConfigResponse)
def get_config(db: Session = Depends(get_db)):
    raw = get_all_config(db)
    config = {k: ConfigItem(**v) for k, v in raw.items()}
    return ConfigResponse(config=config)


@router.post("/")
def update_config(body: ConfigUpdate, db: Session = Depends(get_db)):
    invalid = [k for k in body.config if k not in DEFAULTS]
    if invalid:
        raise HTTPException(status_code=422, detail=f"Unknown config keys: {invalid}")
    set_bulk_config(db, body.config)

    # scan_interval_minutes 변경 시 스케줄러 즉시 반영
    if "scan_interval_minutes" in body.config:
        from app.core.scheduler import reschedule
        try:
            reschedule(int(body.config["scan_interval_minutes"]))
        except Exception:
            pass

    return {"ok": True, "updated": list(body.config.keys())}


# ── 이동 대상 폴더 관리 ───────────────────────────────────

class DestinationFolderBody(BaseModel):
    path: str
    label: Optional[str] = ""


@router.get("/destinations")
def list_destinations(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """등록된 이동 대상 폴더 목록."""
    return {"destinations": get_destination_folders(db)}


@router.post("/destinations")
def add_destination(
    body: DestinationFolderBody,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """이동 대상 폴더 추가."""
    path = body.path.strip()
    if not path:
        raise HTTPException(status_code=422, detail="Path is required")
    folders = get_destination_folders(db)
    # 중복 검사
    if any(f["path"] == path for f in folders):
        raise HTTPException(status_code=409, detail="Path already registered")
    folders.append({"path": path, "label": (body.label or "").strip()})
    set_destination_folders(db, folders)
    return {"ok": True, "destinations": folders}


@router.delete("/destinations/{index}")
def delete_destination(
    index: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """이동 대상 폴더 삭제 (인덱스 기준)."""
    folders = get_destination_folders(db)
    if index < 0 or index >= len(folders):
        raise HTTPException(status_code=404, detail="Index out of range")
    removed = folders.pop(index)
    set_destination_folders(db, folders)
    return {"ok": True, "removed": removed, "destinations": folders}
