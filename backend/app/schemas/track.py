from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TrackOut(BaseModel):
    id: int
    title: str
    artist: Optional[str] = None
    album_artist: Optional[str] = None
    album_title: Optional[str] = None
    track_no: Optional[int] = None
    disc_no: Optional[int] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    duration: Optional[float] = None
    bitrate: Optional[int] = None
    file_path: str
    file_format: Optional[str] = None
    file_size: Optional[int] = None
    has_cover: bool = False
    has_lyrics: bool = False
    album_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrackList(BaseModel):
    total: int
    items: list[TrackOut]


class TrackUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    album_artist: Optional[str] = None
    album_title: Optional[str] = None
    track_no: Optional[int] = None
    disc_no: Optional[int] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    lyrics: Optional[str] = None


class TrackBatchUpdate(BaseModel):
    track_ids: list[int]
    updates: TrackUpdate
