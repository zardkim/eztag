"""
자동 스캔 스케줄러 (APScheduler).
- config DB의 scan_interval_minutes 값에 따라 주기적 스캔 실행
- 설정 변경 시 reschedule() 호출로 즉시 반영
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler(timezone="Asia/Seoul")
_JOB_ID = "auto_scan"


def _run_scan():
    """스케줄러에서 호출되는 스캔 함수."""
    from app.database import SessionLocal
    from app.core.scanner import MusicScanner
    from app.models.scan_log import ScanLog
    from datetime import datetime, timezone

    db = SessionLocal()
    try:
        scan_log = ScanLog(
            scan_type="auto",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        db.add(scan_log)
        db.commit()
        db.refresh(scan_log)

        scanner = MusicScanner(db)
        result = scanner.scan_all()

        scan_log.status = "partial" if result.get("errors", 0) > 0 else "success"
        scan_log.scanned = result.get("scanned", 0)
        scan_log.added = result.get("added", 0)
        scan_log.updated = result.get("updated", 0)
        scan_log.skipped = result.get("skipped", 0)
        scan_log.errors = result.get("errors", 0)
        scan_log.duration = result.get("duration", 0.0)
        scan_log.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"[scheduler] Auto scan complete: {result}")
    except Exception as e:
        logger.error(f"[scheduler] Auto scan failed: {e}")
        try:
            scan_log.status = "error"
            scan_log.error_message = str(e)
            scan_log.finished_at = datetime.now(timezone.utc)
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


def start_scheduler(interval_minutes: int = 0):
    """앱 시작 시 호출. interval_minutes > 0이면 자동 스캔 스케줄 등록."""
    if not _scheduler.running:
        _scheduler.start()
        logger.info("[scheduler] Scheduler started")

    reschedule(interval_minutes)


def reschedule(interval_minutes: int):
    """
    interval_minutes > 0: 스케줄 등록/변경
    interval_minutes == 0: 스케줄 제거 (자동 스캔 비활성화)
    """
    if _scheduler.get_job(_JOB_ID):
        _scheduler.remove_job(_JOB_ID)

    if interval_minutes > 0:
        _scheduler.add_job(
            _run_scan,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=_JOB_ID,
            replace_existing=True,
        )
        logger.info(f"[scheduler] Auto scan scheduled every {interval_minutes} minutes")
    else:
        logger.info("[scheduler] Auto scan disabled")


def get_status() -> dict:
    """현재 스케줄러 상태 반환."""
    job = _scheduler.get_job(_JOB_ID)
    return {
        "running": _scheduler.running,
        "auto_scan_enabled": job is not None,
        "next_run": job.next_run_time.isoformat() if job and job.next_run_time else None,
        "interval_minutes": (
            int(job.trigger.interval.total_seconds() // 60)
            if job and hasattr(job.trigger, "interval")
            else 0
        ),
    }


def shutdown_scheduler():
    """앱 종료 시 호출."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[scheduler] Scheduler stopped")
