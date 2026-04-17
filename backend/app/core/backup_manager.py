"""
백업 및 복원 핵심 로직.
백업 파일: eztag_backup_YYYYMMDD_HHMMSS.tar.gz
  ├── db.dump         (pg_dump --format=custom)  ← DB 전체 (설정, 프리셋 포함)
  └── backup_meta.txt
커버아트는 크기가 크므로 백업에서 제외.
"""
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List
from urllib.parse import urlparse

from app.version import APP_VERSION

BACKUP_DIR = os.environ.get("BACKUP_DIR", "/app/data/backup")


def _parse_db_url(db_url: str) -> dict:
    parsed = urlparse(db_url)
    return {
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "user": parsed.username or "",
        "password": parsed.password or "",
        "dbname": parsed.path.lstrip("/"),
    }


def create_backup(db_url: str) -> str:
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"eztag_backup_v{APP_VERSION}_{timestamp}.tar.gz"
    backup_path = Path(BACKUP_DIR) / backup_name

    db_info = _parse_db_url(db_url)
    env = os.environ.copy()
    env["PGPASSWORD"] = db_info["password"]

    with tempfile.TemporaryDirectory() as tmpdir:
        db_dump_path = Path(tmpdir) / "db.dump"

        # --format=custom: 스키마+데이터 모두 포함, pg_restore로 선택적 복원 가능
        result = subprocess.run(
            [
                "pg_dump",
                "-h", db_info["host"],
                "-p", db_info["port"],
                "-U", db_info["user"],
                "-d", db_info["dbname"],
                "--format=custom",
                "--no-password",
                "-f", str(db_dump_path),
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"pg_dump 실패: {result.stderr}")

        meta_path = Path(tmpdir) / "backup_meta.txt"
        meta_path.write_text(
            f"app_version={APP_VERSION}\n"
            f"backup_format=3.0\n"
            f"timestamp={timestamp}\n"
            f"db_name={db_info['dbname']}\n"
        )

        with tarfile.open(str(backup_path), "w:gz") as tar:
            tar.add(str(db_dump_path), arcname="db.dump")
            tar.add(str(meta_path), arcname="backup_meta.txt")

    return backup_name


def list_backups() -> List[dict]:
    backup_path = Path(BACKUP_DIR)
    if not backup_path.exists():
        return []
    backups = []
    for f in sorted(backup_path.glob("eztag_backup_*.tar.gz"), key=lambda x: x.stat().st_mtime, reverse=True):
        stat = f.stat()
        backups.append({
            "filename": f.name,
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return backups


def _validate_filename(filename: str) -> Path:
    if not filename.endswith(".tar.gz") or "/" in filename or ".." in filename:
        raise ValueError("Invalid backup filename")
    path = Path(BACKUP_DIR) / filename
    if not path.exists():
        raise FileNotFoundError(f"Backup not found: {filename}")
    return path


def delete_backup(filename: str) -> bool:
    path = _validate_filename(filename)
    path.unlink()
    return True


def restore_backup(filename: str, db_url: str) -> dict:
    backup_path = _validate_filename(filename)
    db_info = _parse_db_url(db_url)
    env = os.environ.copy()
    env["PGPASSWORD"] = db_info["password"]

    with tempfile.TemporaryDirectory() as tmpdir:
        with tarfile.open(str(backup_path), "r:gz") as tar:
            tar.extractall(tmpdir)

        db_dump_path = Path(tmpdir) / "db.dump"
        if not db_dump_path.exists():
            raise RuntimeError("백업 파일에 db.dump가 없습니다")

        result = subprocess.run(
            [
                "pg_restore",
                "-h", db_info["host"],
                "-p", db_info["port"],
                "-U", db_info["user"],
                "-d", db_info["dbname"],
                "--clean",
                "--if-exists",
                "--no-password",
                str(db_dump_path),
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode not in (0, 1):
            raise RuntimeError(f"pg_restore 실패: {result.stderr}")

    return {
        "ok": True,
        "filename": filename,
        "warnings": result.stderr[:2000] if result.stderr else "",
    }
