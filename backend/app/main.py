from dotenv import load_dotenv
load_dotenv()

from app.core.logging_config import setup_logging
setup_logging()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.version import APP_VERSION, APP_NAME, BUILD_DATE
from app.config import settings
from app.api import artists, albums, tracks
from app.api import config, logs, backup
from app.api import metadata
from app.api import auth as auth_api, browse as browse_api
from app.api import workspace as workspace_api
from app.api import user_prefs as user_prefs_api
# from app.api import ai_cover as ai_cover_api  # AI 커버아트 (개발 중단)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from pathlib import Path
    import logging
    _log = logging.getLogger(__name__)

    # ── 데이터 폴더 생성 ────────────────────────────────────────
    data_dirs = {
        "library":   os.getenv("LIBRARY_PATH",   "../data/library"),
        "workspace": os.getenv("WORKSPACE_PATH", "../data/workspace"),
        "covers":    os.getenv("COVERS_PATH",    "../data/covers"),
        "logs":      os.getenv("LOG_DIR",        "../data/logs"),
        "backup":    os.getenv("BACKUP_DIR",     "../data/backup"),
    }
    for name, raw_path in data_dirs.items():
        p = Path(raw_path).resolve()
        p.mkdir(parents=True, exist_ok=True)
        _log.info(f"[startup] {name} dir: {p}")

    # 앱 시작 시: DB 없으면 자동 생성
    from sqlalchemy import text
    from sqlalchemy_utils import database_exists, create_database
    from app.config import settings
    if not database_exists(settings.DATABASE_URL):
        _log.info("[startup] Database not found — creating...")
        create_database(settings.DATABASE_URL)
        _log.info("[startup] Database created.")

    # 앱 시작 시: DB 마이그레이션
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "heads")

    from app.database import SessionLocal
    from app.models.scan_folder import ScanFolder
    from app.core.config_store import seed_defaults

    # 설정 기본값 시딩 (DB에 없는 키만 삽입)
    db_seed = SessionLocal()
    try:
        seed_defaults(db_seed)
    finally:
        db_seed.close()

    # data/library 기본 폴더 자동 등록 (browse 경로 검증에 필요)
    # MUSIC_BASE_PATH(Docker) 또는 LIBRARY_PATH 또는 기본값 순으로 사용
    library_path = str(Path(os.getenv("MUSIC_BASE_PATH") or os.getenv("LIBRARY_PATH", "../data/library")).resolve())
    db_lib = SessionLocal()
    try:
        if not db_lib.query(ScanFolder).filter(ScanFolder.path == library_path).first():
            db_lib.add(ScanFolder(path=library_path, name="Library"))
            db_lib.commit()
    finally:
        db_lib.close()

    yield


app = FastAPI(title=f"{APP_NAME} API", version=APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(artists.router)
app.include_router(albums.router)
app.include_router(tracks.router)
app.include_router(config.router)
app.include_router(logs.router)
app.include_router(backup.router)
app.include_router(metadata.router)
app.include_router(auth_api.router)
app.include_router(browse_api.router)
app.include_router(workspace_api.router)
app.include_router(user_prefs_api.router)
# app.include_router(ai_cover_api.router)  # AI 커버아트 (개발 중단)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
        "build_date": BUILD_DATE,
    }
