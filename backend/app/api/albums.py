from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import Optional
import urllib.parse

from app.database import get_db
from app.core.auth import get_current_user
from app.models import Album, Track
from app.schemas.album import AlbumOut, AlbumList, AlbumDetail

router = APIRouter(prefix="/api/albums", tags=["albums"])


@router.get("/", response_model=AlbumList)
def list_albums(
    search: str = Query(None),
    artist_id: int = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Album)
    if search:
        query = query.filter(Album.title.ilike(f"%{search}%"))
    if artist_id:
        query = query.filter(Album.artist_id == artist_id)

    total = query.count()
    items = query.order_by(Album.title).offset((page - 1) * page_size).limit(page_size).all()
    return AlbumList(total=total, items=items)


@router.get("/{album_id}", response_model=AlbumDetail)
def get_album(album_id: int, db: Session = Depends(get_db)):
    album = db.query(Album).options(joinedload(Album.tracks)).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    return album


class AlbumDescriptionBody(BaseModel):
    description: Optional[str] = None


class AlbumEnsureBody(BaseModel):
    title: str
    artist: Optional[str] = None


@router.post("/ensure")
def ensure_album(
    body: AlbumEnsureBody,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """title+artist로 앨범을 조회하거나 없으면 생성 후 album_id를 반환합니다."""
    title = body.title.strip()
    artist = (body.artist or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="title required")
    query = db.query(Album).filter(Album.title == title)
    if artist:
        query = query.filter(Album.album_artist == artist)
    album = query.first()
    if not album:
        album = Album(title=title, album_artist=artist or None)
        db.add(album)
        db.commit()
        db.refresh(album)
    return {"id": album.id, "title": album.title}


@router.patch("/{album_id}/description")
def set_album_description(
    album_id: int,
    body: AlbumDescriptionBody,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """앨범 소개 텍스트를 DB에 저장 (파일 태그 미기록)."""
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    album.description = body.description
    db.commit()
    return {"ok": True, "album_id": album_id}


@router.get("/{album_id}/export-html")
def export_album_html(
    album_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """앨범을 자체 완결형 HTML 파일로 내보내기."""
    from app.core.html_exporter import _cover_to_b64, build_html, track_model_to_dict, _safe_filename

    album = db.query(Album).options(joinedload(Album.tracks)).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    tracks = list(album.tracks)
    track_dicts = [track_model_to_dict(t) for t in tracks]

    # 커버아트 추출
    cover_paths = [t.file_path for t in tracks if t.has_cover]
    cover_b64 = _cover_to_b64(cover_path=album.cover_path, track_paths=cover_paths[:3])

    html = build_html(
        tracks=track_dicts,
        album_title=album.title or "Unknown Album",
        album_artist=album.album_artist,
        year=album.year,
        genre=album.genre,
        cover_b64=cover_b64,
        description=album.description,
    )

    safe_name = _safe_filename(f"{album.title or 'album'} - {album.album_artist or 'unknown'}")
    encoded = urllib.parse.quote(safe_name + ".html")
    return Response(
        content=html.encode("utf-8"),
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )
