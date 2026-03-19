from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Artist, Album
from app.schemas.artist import ArtistOut, ArtistList

router = APIRouter(prefix="/api/artists", tags=["artists"])


@router.get("/", response_model=ArtistList)
def list_artists(
    search: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Artist)
    if search:
        query = query.filter(Artist.name.ilike(f"%{search}%"))
    total = query.count()
    items = query.order_by(Artist.name).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for artist in items:
        album_count = db.query(func.count(Album.id)).filter(Album.artist_id == artist.id).scalar()
        result.append(ArtistOut(
            id=artist.id,
            name=artist.name,
            created_at=artist.created_at,
            album_count=album_count or 0,
        ))

    return ArtistList(total=total, items=result)


@router.get("/{artist_id}", response_model=ArtistOut)
def get_artist(artist_id: int, db: Session = Depends(get_db)):
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    album_count = db.query(func.count(Album.id)).filter(Album.artist_id == artist_id).scalar()
    return ArtistOut(
        id=artist.id,
        name=artist.name,
        created_at=artist.created_at,
        album_count=album_count or 0,
    )
