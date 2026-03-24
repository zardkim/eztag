"""
Scan music folders and populate the database.
"""
import os
import time
import logging
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Artist, Album, Track
from app.models.scan_folder import ScanFolder
from app.core.tag_reader import read_tags
from app.core.tag_writer import write_cover

_LOCAL_COVER_NAMES = ["cover", "folder", "front", "back"]
_LOCAL_COVER_EXTS  = {".jpg", ".jpeg", ".png", ".webp"}
_COVER_MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


def _find_and_embed_local_cover(file_path: str) -> bool:
    """폴더 내 커버 이미지 파일(대소문자 무시)을 찾아 오디오 파일에 임베드. 성공 시 True."""
    from pathlib import Path as _P
    folder = _P(file_path).parent
    try:
        file_map = {f.stem.lower(): f for f in folder.iterdir() if f.suffix.lower() in _LOCAL_COVER_EXTS}
    except Exception:
        return False
    for name in _LOCAL_COVER_NAMES:
        candidate = file_map.get(name)
        if candidate is None:
            continue
        try:
            data = candidate.read_bytes()
        except Exception:
            continue
        if not data:
            continue
        mime = _COVER_MIME.get(candidate.suffix.lower(), "image/jpeg")
        try:
            return write_cover(file_path, data, mime)
        except Exception:
            return False
    return False

logger = logging.getLogger(__name__)

SUPPORTED_EXTS = {".mp3", ".flac", ".m4a", ".aac", ".ogg"}


class MusicScanner:
    def __init__(self, db: Session):
        self.db = db

    def scan_all(self) -> dict:
        """Scan all registered folders."""
        folders = self.db.query(ScanFolder).all()
        total_result = {"scanned": 0, "added": 0, "updated": 0, "skipped": 0, "errors": 0, "duration": 0.0}

        for folder in folders:
            result = self.scan_folder(folder.path)
            for k in total_result:
                if k != "duration":
                    total_result[k] += result[k]

        return total_result

    def scan_folder(self, folder_path: str) -> dict:
        """Scan a single folder recursively."""
        start = time.time()
        result = {"scanned": 0, "added": 0, "updated": 0, "skipped": 0, "errors": 0, "duration": 0.0}

        folder = Path(folder_path)
        if not folder.exists():
            logger.warning(f"Folder not found: {folder_path}")
            result["errors"] += 1
            result["duration"] = time.time() - start
            return result

        for root, _, files in os.walk(folder):
            for fname in files:
                fpath = Path(root) / fname
                if fpath.suffix.lower() not in SUPPORTED_EXTS:
                    continue

                result["scanned"] += 1
                try:
                    action = self._process_file(str(fpath))
                    result[action] += 1
                except Exception as e:
                    logger.error(f"Error processing {fpath}: {e}")
                    result["errors"] += 1

        result["duration"] = round(time.time() - start, 2)
        return result

    def _process_file(self, file_path: str) -> str:
        """Process a single file. Returns 'added', 'updated', or 'skipped'."""
        fpath = Path(file_path)
        mtime = fpath.stat().st_mtime

        existing = self.db.query(Track).filter(Track.file_path == file_path).first()

        if existing:
            if existing.modified_time and abs(existing.modified_time - mtime) < 1.0:
                return "skipped"
            # File changed → re-read tags
            tags = read_tags(file_path)
            self._update_track(existing, tags, mtime)
            return "updated"
        else:
            tags = read_tags(file_path)
            self._add_track(file_path, tags, mtime)
            return "added"

    def _add_track(self, file_path: str, tags: dict, mtime: float):
        artist = self._get_or_create_artist(tags.get("album_artist") or tags.get("artist"))
        album = self._get_or_create_album(tags, artist)

        has_cover = tags.get("has_cover", False)
        if not has_cover:
            has_cover = _find_and_embed_local_cover(file_path)

        track = Track(
            file_path=file_path,
            title=tags.get("title") or Path(file_path).stem,
            artist=tags.get("artist"),
            album_artist=tags.get("album_artist"),
            album_title=tags.get("album_title"),
            track_no=tags.get("track_no"),
            total_tracks=tags.get("total_tracks"),
            disc_no=tags.get("disc_no") or 1,
            year=tags.get("year"),
            release_date=tags.get("release_date"),
            genre=tags.get("genre"),
            label=tags.get("label"),
            isrc=tags.get("isrc"),
            duration=tags.get("duration"),
            bitrate=tags.get("bitrate"),
            sample_rate=tags.get("sample_rate"),
            tag_version=tags.get("tag_version"),
            comment=tags.get("comment"),
            file_format=tags.get("file_format"),
            file_size=tags.get("file_size"),
            modified_time=mtime,
            has_cover=has_cover,
            has_lyrics=tags.get("has_lyrics", False),
            lyrics=tags.get("lyrics"),
            album_id=album.id if album else None,
        )
        self.db.add(track)

        if album:
            album.track_count = (album.track_count or 0) + 1

        self.db.commit()

    def _update_track(self, track: Track, tags: dict, mtime: float):
        track.title = tags.get("title") or Path(track.file_path).stem
        track.artist = tags.get("artist")
        track.album_artist = tags.get("album_artist")
        track.album_title = tags.get("album_title")
        track.track_no = tags.get("track_no")
        track.total_tracks = tags.get("total_tracks")
        track.disc_no = tags.get("disc_no") or 1
        track.year = tags.get("year")
        track.release_date = tags.get("release_date")
        track.genre = tags.get("genre")
        track.label = tags.get("label")
        track.isrc = tags.get("isrc")
        track.duration = tags.get("duration")
        track.bitrate = tags.get("bitrate")
        track.sample_rate = tags.get("sample_rate")
        track.tag_version = tags.get("tag_version")
        track.comment = tags.get("comment")
        track.file_size = tags.get("file_size")
        track.modified_time = mtime
        has_cover = tags.get("has_cover", False)
        if not has_cover:
            has_cover = _find_and_embed_local_cover(track.file_path)
        track.has_cover = has_cover
        track.has_lyrics = tags.get("has_lyrics", False)
        if tags.get("lyrics"):
            track.lyrics = tags.get("lyrics")
        self.db.commit()

    def _get_or_create_artist(self, name: Optional[str]) -> Optional[Artist]:
        if not name or not name.strip():
            return None
        name = name.strip()
        artist = self.db.query(Artist).filter(Artist.name == name).first()
        if not artist:
            artist = Artist(name=name)
            self.db.add(artist)
            self.db.flush()
        return artist

    def _get_or_create_album(self, tags: dict, artist: Optional[Artist]) -> Optional[Album]:
        album_title = tags.get("album_title")
        if not album_title or not album_title.strip():
            return None

        album_title = album_title.strip()
        album_artist_name = (tags.get("album_artist") or tags.get("artist") or "").strip()

        # Match by title + album_artist
        query = self.db.query(Album).filter(Album.title == album_title)
        if album_artist_name:
            query = query.filter(Album.album_artist == album_artist_name)
        album = query.first()

        if not album:
            album = Album(
                title=album_title,
                album_artist=album_artist_name or None,
                year=tags.get("year"),
                genre=tags.get("genre"),
                artist_id=artist.id if artist else None,
                track_count=0,
            )
            self.db.add(album)
            self.db.flush()

        return album

    def cleanup_missing(self) -> int:
        """Remove tracks whose files no longer exist. Returns count removed."""
        removed = 0
        tracks = self.db.query(Track).all()
        for track in tracks:
            if not Path(track.file_path).exists():
                album = track.album
                self.db.delete(track)
                if album:
                    album.track_count = max(0, (album.track_count or 1) - 1)
                    if album.track_count == 0:
                        self.db.delete(album)
                removed += 1
        self.db.commit()

        # Remove artists with no albums
        orphan_artists = self.db.query(Artist).filter(~Artist.albums.any()).all()
        for a in orphan_artists:
            self.db.delete(a)
        self.db.commit()

        return removed
