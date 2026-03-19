"""
Write audio metadata using mutagen.
Supports: MP3, FLAC, M4A (AAC), OGG Vorbis
"""
import logging
from pathlib import Path
from typing import Optional
from mutagen import File as MutagenFile
from mutagen.id3 import TIT2, TPE1, TPE2, TALB, TCON, TRCK, TPOS, TDRC, USLT, TPUB, COMM
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis

logger = logging.getLogger(__name__)


def _resize_cover(image_bytes: bytes, mime_type: str, max_size: int = 1200) -> tuple:
    """이미지를 최대 max_size×max_size로 리사이즈. (bytes, mime_type) 반환."""
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes))
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.LANCZOS)
        # RGBA/P → RGB for JPEG
        if img.mode in ("RGBA", "P") and ("jpeg" in mime_type or "jpg" in mime_type):
            img = img.convert("RGB")
        output = io.BytesIO()
        fmt = "JPEG" if "jpeg" in mime_type or "jpg" in mime_type else "PNG"
        img.save(output, format=fmt, quality=92)
        return output.getvalue(), mime_type
    except Exception as e:
        logger.warning(f"[tag_writer] could not resize cover: {e}")
        return image_bytes, mime_type


def write_cover(file_path: str, image_bytes: bytes, mime_type: str, cover_type: int = 3) -> bool:
    """오디오 파일에 커버아트를 임베드. 기존 커버는 교체. cover_type은 APIC 타입 (기본 3=Front Cover)."""
    path = Path(file_path)
    ext = path.suffix.lower().lstrip(".")
    try:
        # 리사이즈 (최대 1200×1200)
        image_bytes, mime_type = _resize_cover(image_bytes, mime_type)

        audio = MutagenFile(file_path, easy=False)
        if audio is None:
            return False

        if ext == "mp3":
            from mutagen.id3 import APIC
            if audio.tags is None:
                audio.add_tags()
            # 같은 타입의 APIC만 삭제 (다른 타입 유지)
            existing = audio.tags.getall("APIC")
            kept = [f for f in existing if f.type != cover_type]
            audio.tags.delall("APIC")
            for f in kept:
                audio.tags.add(f)
            audio.tags.add(APIC(encoding=3, mime=mime_type, type=cover_type, desc="Cover", data=image_bytes))

        elif ext == "flac":
            from mutagen.flac import Picture
            # 같은 타입의 Picture만 삭제 (다른 타입 유지)
            existing = audio.pictures
            audio.clear_pictures()
            for p in existing:
                if p.type != cover_type:
                    audio.add_picture(p)
            pic = Picture()
            pic.type = cover_type
            pic.mime = mime_type
            pic.desc = "Cover"
            pic.data = image_bytes
            audio.add_picture(pic)

        elif ext in ("m4a", "aac", "mp4"):
            from mutagen.mp4 import MP4Cover
            fmt = MP4Cover.FORMAT_PNG if "png" in mime_type else MP4Cover.FORMAT_JPEG
            if audio.tags is None:
                audio.add_tags()
            audio.tags["covr"] = [MP4Cover(image_bytes, imageformat=fmt)]

        elif ext == "ogg":
            import base64
            from mutagen.flac import Picture
            # 같은 타입의 Picture만 삭제 (다른 타입 유지)
            existing_encoded = audio.get("metadata_block_picture", [])
            kept_encoded = []
            for enc in existing_encoded:
                try:
                    p = Picture(base64.b64decode(enc))
                    if p.type != cover_type:
                        kept_encoded.append(enc)
                except Exception:
                    pass
            pic = Picture()
            pic.type = cover_type
            pic.mime = mime_type
            pic.desc = "Cover"
            pic.data = image_bytes
            kept_encoded.append(base64.b64encode(pic.write()).decode("ascii"))
            audio["metadata_block_picture"] = kept_encoded

        else:
            return False

        audio.save()
        return True
    except Exception as e:
        logger.error(f"[tag_writer] Error writing cover {file_path}: {e}")
        return False


def remove_cover(file_path: str) -> bool:
    """오디오 파일에서 모든 커버아트를 제거."""
    path = Path(file_path)
    ext = path.suffix.lower().lstrip(".")
    try:
        audio = MutagenFile(file_path, easy=False)
        if audio is None:
            return False
        if ext == "mp3":
            if audio.tags:
                audio.tags.delall("APIC")
        elif ext == "flac":
            audio.clear_pictures()
        elif ext in ("m4a", "aac", "mp4"):
            if audio.tags and "covr" in audio.tags:
                del audio.tags["covr"]
        elif ext == "ogg":
            if "metadata_block_picture" in audio:
                del audio["metadata_block_picture"]
        else:
            return False
        audio.save()
        return True
    except Exception as e:
        logger.error(f"[tag_writer] Error removing cover {file_path}: {e}")
        return False


def write_tags(file_path: str, updates: dict, clear_fields: list = None) -> bool:
    """
    Write tags to an audio file.
    updates: dict with keys matching TrackUpdate fields.
    clear_fields: list of field names to explicitly clear/delete.
    Returns True on success.
    """
    path = Path(file_path)
    ext = path.suffix.lower().lstrip(".")
    clear = set(clear_fields) if clear_fields else set()

    try:
        audio = MutagenFile(file_path, easy=False)
        if audio is None:
            return False

        if ext == "mp3":
            _write_mp3(audio, updates)
            if clear:
                _clear_mp3(audio, clear)
        elif ext == "flac":
            _write_flac(audio, updates)
            if clear:
                _clear_flac(audio, clear)
        elif ext in ("m4a", "aac", "mp4"):
            _write_m4a(audio, updates)
            if clear:
                _clear_m4a(audio, clear)
        elif ext == "ogg":
            _write_ogg(audio, updates)
            if clear:
                _clear_ogg(audio, clear)
        else:
            return False

        audio.save()
        return True

    except Exception as e:
        logger.error(f"[tag_writer] Error writing {file_path}: {e}")
        return False


def _set_if(updates, key, fn):
    val = updates.get(key)
    if val is not None:
        fn(val)


def _write_mp3(audio, updates: dict):
    from mutagen.id3 import ID3

    if audio.tags is None:
        audio.add_tags()
    tags = audio.tags

    _set_if(updates, "title",        lambda v: tags.setall("TIT2", [TIT2(encoding=3, text=v)]))
    _set_if(updates, "artist",       lambda v: tags.setall("TPE1", [TPE1(encoding=3, text=v)]))
    _set_if(updates, "album_artist", lambda v: tags.setall("TPE2", [TPE2(encoding=3, text=v)]))
    _set_if(updates, "album_title",  lambda v: tags.setall("TALB", [TALB(encoding=3, text=v)]))
    _set_if(updates, "genre",        lambda v: tags.setall("TCON", [TCON(encoding=3, text=v)]))
    _set_if(updates, "label",        lambda v: tags.setall("TPUB", [TPUB(encoding=3, text=v)]))
    _set_if(updates, "disc_no",      lambda v: tags.setall("TPOS", [TPOS(encoding=3, text=str(v))]))

    # release_date 우선, 없으면 year
    date_val = updates.get("release_date") or (str(updates["year"]) if updates.get("year") else None)
    if date_val:
        tags.setall("TDRC", [TDRC(encoding=3, text=date_val)])

    # track_no/total_tracks → "N/T" 형식
    track_no = updates.get("track_no")
    total_tracks = updates.get("total_tracks")
    if track_no is not None:
        trck = f"{track_no}/{total_tracks}" if total_tracks else str(track_no)
        tags.setall("TRCK", [TRCK(encoding=3, text=trck)])

    lyrics = updates.get("lyrics")
    if lyrics is not None:
        tags.setall("USLT", [USLT(encoding=3, lang="eng", desc="", text=lyrics)])

    comment = updates.get("comment")
    if comment is not None:
        tags.setall("COMM", [COMM(encoding=3, lang="eng", desc="", text=comment)])


def _write_flac(audio, updates: dict):
    if audio.tags is None:
        audio.add_tags()

    mapping = {
        "title":        "title",
        "artist":       "artist",
        "album_artist": "albumartist",
        "album_title":  "album",
        "genre":        "genre",
        "lyrics":       "lyrics",
        "label":        "organization",
        "comment":      "comment",
    }
    for src, dst in mapping.items():
        val = updates.get(src)
        if val is not None:
            audio.tags[dst] = [val]

    # release_date 우선, 없으면 year
    date_val = updates.get("release_date") or (str(updates["year"]) if updates.get("year") else None)
    if date_val:
        audio.tags["date"] = [date_val]

    if updates.get("track_no") is not None:
        audio.tags["tracknumber"] = [str(updates["track_no"])]
    if updates.get("total_tracks") is not None:
        audio.tags["tracktotal"] = [str(updates["total_tracks"])]
    if updates.get("disc_no") is not None:
        audio.tags["discnumber"] = [str(updates["disc_no"])]


def _write_m4a(audio, updates: dict):
    if audio.tags is None:
        audio.add_tags()

    mapping = {
        "title":        "\xa9nam",
        "artist":       "\xa9ART",
        "album_artist": "aART",
        "album_title":  "\xa9alb",
        "genre":        "\xa9gen",
        "lyrics":       "\xa9lyr",
        "label":        "\xa9pub",
        "comment":      "\xa9cmt",
    }
    for src, dst in mapping.items():
        val = updates.get(src)
        if val is not None:
            audio.tags[dst] = [val]

    # release_date 우선, 없으면 year
    date_val = updates.get("release_date") or (str(updates["year"]) if updates.get("year") else None)
    if date_val:
        audio.tags["\xa9day"] = [date_val]

    track_no = updates.get("track_no")
    total_tracks = updates.get("total_tracks") or 0
    if track_no is not None:
        audio.tags["trkn"] = [(track_no, total_tracks)]
    if updates.get("disc_no") is not None:
        audio.tags["disk"] = [(updates["disc_no"], 0)]


def _write_ogg(audio, updates: dict):
    mapping = {
        "title":        "title",
        "artist":       "artist",
        "album_artist": "albumartist",
        "album_title":  "album",
        "genre":        "genre",
        "lyrics":       "lyrics",
        "label":        "organization",
        "comment":      "comment",
    }
    for src, dst in mapping.items():
        val = updates.get(src)
        if val is not None:
            audio[dst] = [val]

    # release_date 우선, 없으면 year
    date_val = updates.get("release_date") or (str(updates["year"]) if updates.get("year") else None)
    if date_val:
        audio["date"] = [date_val]

    if updates.get("track_no") is not None:
        audio["tracknumber"] = [str(updates["track_no"])]
    if updates.get("total_tracks") is not None:
        audio["tracktotal"] = [str(updates["total_tracks"])]
    if updates.get("disc_no") is not None:
        audio["discnumber"] = [str(updates["disc_no"])]


# ── 필드 삭제 헬퍼 ────────────────────────────────────────────────────────────

def _clear_mp3(audio, fields: set):
    """MP3 ID3 태그 특정 필드 삭제."""
    if audio.tags is None:
        return
    mapping = {
        "title":        "TIT2",
        "artist":       "TPE1",
        "album_artist": "TPE2",
        "album_title":  "TALB",
        "genre":        "TCON",
        "label":        "TPUB",
        "disc_no":      "TPOS",
        "year":         "TDRC",
        "release_date": "TDRC",
        "track_no":     "TRCK",
        "total_tracks": "TRCK",
        "lyrics":       "USLT",
        "comment":      "COMM",
    }
    deleted = set()
    for field in fields:
        tag = mapping.get(field)
        if tag and tag not in deleted:
            audio.tags.delall(tag)
            deleted.add(tag)


def _clear_flac(audio, fields: set):
    """FLAC Vorbis 태그 특정 필드 삭제."""
    if audio.tags is None:
        return
    mapping = {
        "title":        "title",
        "artist":       "artist",
        "album_artist": "albumartist",
        "album_title":  "album",
        "genre":        "genre",
        "lyrics":       "lyrics",
        "label":        "organization",
        "year":         "date",
        "release_date": "date",
        "track_no":     "tracknumber",
        "total_tracks": "tracktotal",
        "disc_no":      "discnumber",
        "comment":      "comment",
    }
    deleted = set()
    for field in fields:
        tag = mapping.get(field)
        if tag and tag not in deleted:
            if tag in audio.tags:
                del audio.tags[tag]
            deleted.add(tag)


def _clear_m4a(audio, fields: set):
    """M4A 태그 특정 필드 삭제."""
    if audio.tags is None:
        return
    mapping = {
        "title":        "\xa9nam",
        "artist":       "\xa9ART",
        "album_artist": "aART",
        "album_title":  "\xa9alb",
        "genre":        "\xa9gen",
        "lyrics":       "\xa9lyr",
        "label":        "\xa9pub",
        "year":         "\xa9day",
        "release_date": "\xa9day",
        "track_no":     "trkn",
        "total_tracks": "trkn",
        "disc_no":      "disk",
        "comment":      "\xa9cmt",
    }
    deleted = set()
    for field in fields:
        tag = mapping.get(field)
        if tag and tag not in deleted:
            if tag in audio.tags:
                del audio.tags[tag]
            deleted.add(tag)


def _clear_ogg(audio, fields: set):
    """OGG Vorbis 태그 특정 필드 삭제."""
    mapping = {
        "title":        "title",
        "artist":       "artist",
        "album_artist": "albumartist",
        "album_title":  "album",
        "genre":        "genre",
        "lyrics":       "lyrics",
        "label":        "organization",
        "year":         "date",
        "release_date": "date",
        "track_no":     "tracknumber",
        "total_tracks": "tracktotal",
        "disc_no":      "discnumber",
        "comment":      "comment",
    }
    deleted = set()
    for field in fields:
        tag = mapping.get(field)
        if tag and tag not in deleted:
            if tag in audio:
                del audio[tag]
            deleted.add(tag)
