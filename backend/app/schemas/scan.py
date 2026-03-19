from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ScanFolderCreate(BaseModel):
    path: str
    name: Optional[str] = None


class ScanFolderOut(BaseModel):
    id: int
    path: str
    name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScanResult(BaseModel):
    scanned: int = 0
    added: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    duration: float = 0.0
