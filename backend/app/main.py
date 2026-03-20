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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 앱 시작 시: DB 마이그레이션
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "heads")

    from app.database import SessionLocal
    from app.models.scan_folder import ScanFolder
    from pathlib import Path

    # data/library 기본 폴더 자동 등록 (browse 경로 검증에 필요)
    library_path = str(Path(os.getenv("LIBRARY_PATH", "../data/library")).resolve())
    Path(library_path).mkdir(parents=True, exist_ok=True)
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


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
        "build_date": BUILD_DATE,
    }
