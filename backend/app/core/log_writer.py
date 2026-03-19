"""활동 로그 기록 헬퍼."""
import logging
from typing import Optional

_log = logging.getLogger(__name__)


def write_activity_log(
    db,
    log_type: str,
    message: str,
    action: Optional[str] = None,
    file_path: Optional[str] = None,
    username: Optional[str] = None,
    detail: Optional[str] = None,
) -> None:
    """activity_log 테이블에 로그를 기록한다. 실패해도 예외를 발생시키지 않는다."""
    try:
        from app.models.activity_log import ActivityLog
        entry = ActivityLog(
            log_type=log_type,
            action=action,
            message=message,
            file_path=file_path,
            username=username,
            detail=detail,
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        _log.warning(f"[log_writer] Failed to write activity log: {e}")
        try:
            db.rollback()
        except Exception:
            pass
