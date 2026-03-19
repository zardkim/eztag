from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import hashlib

from app.database import get_db
from app.models import Album, Track
from app.config import settings

router = APIRouter(prefix="/api/covers", tags=["covers"])


@router.get("/album/{album_id}")
def get_album_cover(album_id: int, db: Session = Depends(get_db)):
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album or not album.cover_path:
        raise HTTPException(status_code=404, detail="Cover not found")
    return {"cover_url": f"/covers/{album.cover_path}"}


@router.post("/album/{album_id}")
async def upload_album_cover(
    album_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    data = await file.read()
    ext = "jpg" if "jpeg" in (file.content_type or "") else "png"
    digest = hashlib.md5(data).hexdigest()
    subdir = digest[:2]
    filename = f"{digest}.{ext}"

    save_dir = Path(settings.COVERS_PATH) / subdir
    save_dir.mkdir(parents=True, exist_ok=True)
    (save_dir / filename).write_bytes(data)

    album.cover_path = f"{subdir}/{filename}"
    db.commit()
    return {"cover_url": f"/covers/{album.cover_path}"}


@router.delete("/album/{album_id}")
def delete_album_cover(album_id: int, db: Session = Depends(get_db)):
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    if album.cover_path:
        cover_file = Path(settings.COVERS_PATH) / album.cover_path
        if cover_file.exists():
            cover_file.unlink()
        album.cover_path = None
        db.commit()

    return {"ok": True}
