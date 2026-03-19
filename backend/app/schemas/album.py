from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AlbumOut(BaseModel):
    id: int
    title: str
    album_artist: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    cover_path: Optional[str] = None
    track_count: int = 0
    artist_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlbumList(BaseModel):
    total: int
    items: list[AlbumOut]


class TrackInAlbum(BaseModel):
    id: int
    title: str
    artist: Optional[str] = None
    track_no: Optional[int] = None
    disc_no: Optional[int] = None
    duration: Optional[float] = None
    file_path: str
    file_format: Optional[str] = None
    has_cover: bool = False
    has_lyrics: bool = False

    class Config:
        from_attributes = True


class AlbumDetail(AlbumOut):
    tracks: list[TrackInAlbum] = []
