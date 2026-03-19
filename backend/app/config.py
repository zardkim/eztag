from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://eztag:eztag@localhost:5432/eztag"
    MUSIC_BASE_PATH: str = "/music"
    COVERS_PATH: str = "/app/data/covers"
    SECRET_KEY: str = "changeme"
    TOKEN_EXPIRE_DAYS: int = 30
    BACKEND_URL: str = "http://localhost:18011"
    FRONTEND_URL: str = "http://localhost:5850"
    ALLOWED_EXTENSIONS: List[str] = [".mp3", ".flac", ".m4a", ".ogg"]
    COVER_SIZE: int = 500  # px, cover thumbnail size
    LOG_DIR: str = "/app/data/logs"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
