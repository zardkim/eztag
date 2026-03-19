from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import get_db
from app.models import Track
from app.schemas.track import TrackOut, TrackList, TrackUpdate, TrackBatchUpdate
from app.core.tag_writer import write_tags
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/tracks", tags=["tracks"])


@router.get("/", response_model=TrackList)
def list_tracks(
    search: str = Query(None),
    album_id: int = Query(None),
    artist: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Track)
    if search:
        query = query.filter(
            Track.title.ilike(f"%{search}%") |
            Track.artist.ilike(f"%{search}%") |
            Track.album_title.ilike(f"%{search}%")
        )
    if album_id:
        query = query.filter(Track.album_id == album_id)
    if artist:
        query = query.filter(Track.artist.ilike(f"%{artist}%"))

    total = query.count()
    items = (
        query
        .order_by(Track.album_title, Track.disc_no, Track.track_no, Track.title)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return TrackList(total=total, items=items)


@router.get("/{track_id}", response_model=TrackOut)
def get_track(track_id: int, db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track


@router.get("/{track_id}/lyrics")
def get_lyrics(track_id: int, db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return {"track_id": track_id, "lyrics": track.lyrics or ""}


@router.patch("/{track_id}", response_model=TrackOut)
def update_track(track_id: int, body: TrackUpdate, db: Session = Depends(get_db),
                 current_user=Depends(get_current_user)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    updates = body.model_dump(exclude_none=True)
    if not updates:
        return track

    # Write to file
    ok = write_tags(track.file_path, updates)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to write tags to file")

    # Update DB
    for k, v in updates.items():
        setattr(track, k, v)
    if "lyrics" in updates:
        track.has_lyrics = bool(updates["lyrics"])

    db.commit()
    db.refresh(track)

    # 활동 로그
    from app.core.log_writer import write_activity_log
    fields_str = ", ".join(updates.keys())
    fname = Path(track.file_path).name if track.file_path else str(track_id)
    write_activity_log(db, "tag_write", f"트랙 태그 저장: {fname} [{fields_str}]",
                       action="update_track", file_path=track.file_path,
                       username=getattr(current_user, "username", None))

    return track


@router.post("/batch-update")
def batch_update_tracks(body: TrackBatchUpdate, db: Session = Depends(get_db)):
    updates = body.updates.model_dump(exclude_none=True)
    if not updates:
        return {"updated": 0}

    updated = 0
    errors = []

    for track_id in body.track_ids:
        track = db.query(Track).filter(Track.id == track_id).first()
        if not track:
            errors.append({"id": track_id, "error": "Not found"})
            continue

        ok = write_tags(track.file_path, updates)
        if not ok:
            errors.append({"id": track_id, "error": "Failed to write tags"})
            continue

        for k, v in updates.items():
            setattr(track, k, v)
        updated += 1

    db.commit()
    return {"updated": updated, "errors": errors}
