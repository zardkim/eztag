from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.scheduler import get_status, reschedule
from app.core.config_store import get_config

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.get("/status")
def scheduler_status():
    return get_status()


@router.post("/trigger")
def trigger_scan():
    """즉시 스캔 실행 (별도 스레드)."""
    import threading
    from app.core.scheduler import _run_scan
    t = threading.Thread(target=_run_scan, daemon=True)
    t.start()
    return {"ok": True, "message": "스캔이 시작되었습니다"}


@router.post("/apply-config")
def apply_config(db: Session = Depends(get_db)):
    """config DB의 scan_interval_minutes를 스케줄러에 즉시 반영."""
    minutes = int(get_config(db, "scan_interval_minutes") or "0")
    reschedule(minutes)
    return get_status()
