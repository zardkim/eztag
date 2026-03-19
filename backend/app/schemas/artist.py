from pydantic import BaseModel
from datetime import datetime


class ArtistOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    album_count: int = 0

    class Config:
        from_attributes = True


class ArtistList(BaseModel):
    total: int
    items: list[ArtistOut]
