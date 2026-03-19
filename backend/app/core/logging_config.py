"""Python logging 설정. main.py 최상단에서 setup_logging() 호출."""
import logging
import logging.handlers
import os
from pathlib import Path

LOG_DIR = os.environ.get("LOG_DIR", "/app/data/logs")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5


def setup_logging():
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 콘솔
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    # 앱 전체 로그 (rotating)
    fh = logging.handlers.RotatingFileHandler(
        Path(LOG_DIR) / "app.log",
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    # 에러 전용 로그
    eh = logging.handlers.RotatingFileHandler(
        Path(LOG_DIR) / "error.log",
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    eh.setLevel(logging.ERROR)
    eh.setFormatter(fmt)

    # 노이즈 억제
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    root.handlers.clear()
    root.addHandler(ch)
    root.addHandler(fh)
    root.addHandler(eh)
