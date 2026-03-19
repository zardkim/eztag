from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ScanLogOut(BaseModel):
    id: int
    scan_type: str
    status: str
    folder_path: Optional[str] = None
    scanned: int
    added: int
    updated: int
    skipped: int
    errors: int
    duration: float
    error_message: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScanLogList(BaseModel):
    total: int
    items: List[ScanLogOut]


class ActivityLogOut(BaseModel):
    id: int
    log_type: str
    action: Optional[str] = None
    message: Optional[str] = None
    file_path: Optional[str] = None
    username: Optional[str] = None
    detail: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityLogList(BaseModel):
    total: int
    items: List[ActivityLogOut]
