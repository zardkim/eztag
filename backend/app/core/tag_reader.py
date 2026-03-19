"""
Read audio metadata using mutagen.
Supports: MP3, FLAC, M4A (AAC), OGG Vorbis
"""
import os
from pathlib import Path
from typing import Optional, Tuple
from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
from mutagen.id3 import ID3NoHeaderError


def extract_cover_at(file_path: str, index: int = 0) -> Optional[Tuple[bytes, str]]:
    """파일에서 index번째 커버아트를 추출."""
    try:
        ext = Path(file_path).suffix.lower().lstrip(".")
        audio = MutagenFile(file_path, easy=False)
        if audio is None:
            return None

        if ext == "mp3":
            tags = audio.tags
            if not tags:
                return None
            apic_keys = sorted(k for k in tags.keys() if k.startswith("APIC"))
            if index < len(apic_keys):
                apic = tags[apic_keys[index]]
                return (apic.data, apic.mime or "image/jpeg")

        elif ext == "flac":
            if index < len(audio.pictures):
                pic = audio.pictures[index]
                return (pic.data, pic.mime or "image/jpeg")

        elif ext in ("m4a", "aac", "mp4"):
            tags = audio.tags
            if tags and "covr" in tags and index < len(tags["covr"]):
                from mutagen.mp4 import MP4Cover
                data = bytes(tags["covr"][index])
                mime = "image/png" if tags["covr"][index].imageformat == MP4Cover.FORMAT_PNG else "image/jpeg"
                return (data, mime)

        elif ext == "ogg":
            import base64, struct
            pic_tags = audio.get("metadata_block_picture")
            if pic_tags and index < len(pic_tags):
                raw = base64.b64decode(pic_tags[index])
                offset = 4
                mime_len = struct.unpack(">I", raw[offset:offset+4])[0]; offset += 4
                mime = raw[offset:offset+mime_len].decode(); offset += mime_len
                desc_len = struct.unpack(">I", raw[offset:offset+4])[0]; offset += 4 + desc_len
                offset += 16
                data_len = struct.unpack(">I", raw[offset:offset+4])[0]; offset += 4
                return (raw[offset:offset+data_len], mime)

    except Exception:
        pass
    return None


def _get_image_info(data: bytes) -> dict:
    """이미지 bytes에서 width, height, size_bytes 추출."""
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(data))
        return {"width": img.width, "height": img.height, "size_bytes": len(data)}
    except Exception:
        return {"width": 0, "height": 0, "size_bytes": len(data)}


def list_covers(file_path: str) -> list:
    """파일에 내장된 모든 커버 정보 목록 반환. (width, height, size_bytes 포함)"""
    APIC_TYPES = {
        0: "기타", 1: "파일 아이콘", 2: "아이콘", 3: "앞면 커버",
        4: "뒷면 커버", 5: "리플렛", 6: "미디어", 7: "리드 아티스트",
        8: "아티스트", 9: "지휘자", 10: "밴드", 11: "작곡가",
        12: "작사가", 13: "녹음 장소", 14: "공연 중",
        15: "화면 캡처", 16: "컬러 피쉬", 17: "삽화",
        18: "밴드 로고타입", 19: "스튜디오 로고타입",
    }
    covers = []
    try:
        ext = Path(file_path).suffix.lower().lstrip(".")
        audio = MutagenFile(file_path, easy=False)
        if audio is None:
            return covers

        if ext == "mp3":
            tags = audio.tags
            if tags:
                for i, key in enumerate(sorted(k for k in tags.keys() if k.startswith("APIC"))):
                    apic = tags[key]
                    covers.append({
                        "index": i,
                        "type_id": apic.type,
                        "type_name": APIC_TYPES.get(apic.type, f"타입 {apic.type}"),
                        "mime": apic.mime or "image/jpeg",
                        **_get_image_info(apic.data),
                    })
        elif ext == "flac":
            for i, pic in enumerate(audio.pictures):
                covers.append({
                    "index": i,
                    "type_id": pic.type,
                    "type_name": APIC_TYPES.get(pic.type, f"타입 {pic.type}"),
                    "mime": pic.mime or "image/jpeg",
                    **_get_image_info(pic.data),
                })
        elif ext in ("m4a", "aac", "mp4"):
            tags = audio.tags
            if tags and "covr" in tags:
                for i, covr_item in enumerate(tags["covr"]):
                    data = bytes(covr_item)
                    covers.append({
                        "index": i,
                        "type_id": 3,
                        "type_name": "앞면 커버",
                        "mime": "image/jpeg",
                        **_get_image_info(data),
                    })
        elif ext == "ogg":
            import base64, struct
            pic_tags = audio.get("metadata_block_picture")
            if pic_tags:
                for i, pic_tag in enumerate(pic_tags):
                    try:
                        raw = base64.b64decode(pic_tag)
                        offset = 0
                        pic_type = struct.unpack(">I", raw[offset:offset+4])[0]; offset += 4
                        mime_len = struct.unpack(">I", raw[offset:offset+4])[0]; offset += 4
                        mime = raw[offset:offset+mime_len].decode(); offset += mime_len
                        desc_len = struct.unpack(">I", raw[offset:offset+4])[0]; offset += 4 + desc_len
                        offset += 16
                        data_len = struct.unpack(">I", raw[offset:offset+4])[0]; offset += 4
                        data = raw[offset:offset+data_len]
                        covers.append({
                            "index": i,
                            "type_id": pic_type,
                            "type_name": APIC_TYPES.get(pic_type, f"타입 {pic_type}"),
                            "mime": mime or "image/jpeg",
                            **_get_image_info(data),
                        })
                    except Exception:
                        covers.append({"index": i, "type_id": 3, "type_name": "앞면 커버", "mime": "image/jpeg", "width": 0, "height": 0, "size_bytes": 0})
    except Exception:
        pass
    return covers


def extract_cover(file_path: str) -> Optional[Tuple[bytes, str]]:
    """파일에서 커버아트를 추출. (bytes, mime_type) 또는 None 반환."""
    try:
        ext = Path(file_path).suffix.lower().lstrip(".")
        audio = MutagenFile(file_path, easy=False)
        if audio is None:
            return None

        if ext == "mp3":
            tags = audio.tags
            if not tags:
                return None
            for key in tags.keys():
                if key.startswith("APIC"):
                    apic = tags[key]
                    return (apic.data, apic.mime or "image/jpeg")

        elif ext == "flac":
            if audio.pictures:
                pic = audio.pictures[0]
                return (pic.data, pic.mime or "image/jpeg")

        elif ext in ("m4a", "aac", "mp4"):
            tags = audio.tags
            if tags and "covr" in tags:
                covr = tags["covr"]
                if covr:
                    data = bytes(covr[0])
                    # MP4Cover format 값으로 mime 판별
                    from mutagen.mp4 import MP4Cover
                    mime = "image/png" if covr[0].imageformat == MP4Cover.FORMAT_PNG else "image/jpeg"
                    return (data, mime)

        elif ext == "ogg":
            # OGG: METADATA_BLOCK_PICTURE (base64)
            import base64
            import struct
            tags = audio
            pic_tag = tags.get("metadata_block_picture")
            if pic_tag:
                raw = base64.b64decode(pic_tag[0])
                # FLAC picture block 파싱
                offset = 4  # picture type
                mime_len = struct.unpack(">I", raw[offset:offset+4])[0]; offset += 4
                mime = raw[offset:offset+mime_len].decode(); offset += mime_len
                desc_len = struct.unpack(">I", raw[offset:offset+4])[0]; offset += 4 + desc_len
                offset += 16  # width, height, depth, colors
                data_len = struct.unpack(">I", raw[offset:offset+4])[0]; offset += 4
                return (raw[offset:offset+data_len], mime)

    except Exception:
        pass
    return None


def _get_tag(tags, *keys, default=None):
    """Try multiple tag keys and return the first found value."""
    for key in keys:
        val = tags.get(key)
        if val:
            if isinstance(val, list):
                return str(val[0]).strip() if val[0] else default
            return str(val).strip() if val else default
    return default


def _to_int(value) -> Optional[int]:
    try:
        if value is None:
            return None
        s = str(value).split("/")[0].strip()
        return int(s) if s else None
    except (ValueError, TypeError):
        return None


def read_tags(file_path: str) -> dict:
    """
    Read tags from an audio file.
    Returns a dict with normalized tag fields.
    """
    path = Path(file_path)
    ext = path.suffix.lower().lstrip(".")

    result = {
        "title": None,
        "artist": None,
        "album_artist": None,
        "album_title": None,
        "track_no": None,
        "total_tracks": None,
        "disc_no": None,
        "year": None,
        "release_date": None,
        "genre": None,
        "label": None,
        "isrc": None,
        "duration": None,
        "bitrate": None,
        "sample_rate": None,
        "tag_version": None,
        "comment": None,
        "file_format": ext,
        "file_size": path.stat().st_size if path.exists() else None,
        "modified_time": path.stat().st_mtime if path.exists() else None,
        "has_cover": False,
        "has_lyrics": False,
        "lyrics": None,
    }

    try:
        audio = MutagenFile(file_path, easy=False)
        if audio is None:
            return result

        # Duration, bitrate, sample_rate
        if hasattr(audio, "info"):
            info = audio.info
            result["duration"] = getattr(info, "length", None)
            result["sample_rate"] = getattr(info, "sample_rate", None)
            raw_bitrate = getattr(info, "bitrate", None)
            # mutagen은 포맷마다 bps 또는 kbps로 반환 → 1000 이상이면 bps로 판단해 kbps로 변환
            if raw_bitrate and raw_bitrate >= 1000:
                result["bitrate"] = round(raw_bitrate / 1000)
            else:
                result["bitrate"] = raw_bitrate

        if ext == "mp3":
            _read_mp3(audio, result)
        elif ext == "flac":
            _read_flac(audio, result)
        elif ext in ("m4a", "aac", "mp4"):
            _read_m4a(audio, result)
        elif ext == "ogg":
            _read_ogg(audio, result)

    except Exception:
        pass

    return result


def _read_mp3(audio, result: dict):
    tags = audio.tags
    if not tags:
        return

    def first(tag):
        v = tags.get(tag)
        if v is None:
            return None
        # ID3 frame 객체는 .text 리스트를 가짐
        if hasattr(v, "text"):
            return str(v.text[0]).strip() if v.text else None
        # fallback: 직접 str 변환
        return str(v).strip() or None

    result["title"] = first("TIT2")
    result["artist"] = first("TPE1")
    result["album_artist"] = first("TPE2")
    result["album_title"] = first("TALB")
    result["genre"] = first("TCON")

    # Track number / total tracks (TRCK: "3" or "3/10")
    trck = first("TRCK")
    if trck:
        parts = str(trck).split("/")
        result["track_no"] = _to_int(parts[0])
        if len(parts) > 1:
            result["total_tracks"] = _to_int(parts[1])

    # Disc number
    tpos = first("TPOS")
    result["disc_no"] = _to_int(tpos)

    # Year / release date
    tdrc = first("TDRC") or first("TYER")
    if tdrc:
        s = str(tdrc).strip()
        result["year"] = _to_int(s[:4])
        if len(s) >= 10:          # YYYY-MM-DD 형식이면 발매일도 저장
            result["release_date"] = s[:10]

    # Label (publisher)
    result["label"] = first("TPUB")

    # ISRC
    result["isrc"] = first("TSRC")

    # Lyrics (USLT)
    for key in tags.keys():
        if key.startswith("USLT"):
            uslt = tags[key]
            # USLT.text는 str, USLT.text가 없으면 str() 변환
            lyr = uslt.text if hasattr(uslt, "text") else str(uslt)
            if lyr:
                result["lyrics"] = lyr
                result["has_lyrics"] = True
            break

    # Cover art (APIC)
    for key in tags.keys():
        if key.startswith("APIC"):
            result["has_cover"] = True
            break

    # Comment (COMM)
    for key in tags.keys():
        if key.startswith("COMM:"):
            comm = tags[key]
            text = comm.text[0] if hasattr(comm, "text") and comm.text else str(comm)
            if text:
                result["comment"] = str(text).strip()
            break

    # Tag version (ID3 version)
    try:
        v = tags.version  # tuple e.g. (2, 4, 0)
        result["tag_version"] = f"ID3v{v[0]}.{v[1]}"
    except Exception:
        pass


def _read_flac(audio, result: dict):
    tags = audio.tags
    if not tags:
        return

    result["title"] = _get_tag(tags, "title")
    result["artist"] = _get_tag(tags, "artist")
    result["album_artist"] = _get_tag(tags, "albumartist", "album artist")
    result["album_title"] = _get_tag(tags, "album")
    result["genre"] = _get_tag(tags, "genre")
    result["label"] = _get_tag(tags, "organization", "label", "publisher")
    result["isrc"] = _get_tag(tags, "isrc")

    # Track / total tracks
    trck = _get_tag(tags, "tracknumber")
    if trck:
        parts = str(trck).split("/")
        result["track_no"] = _to_int(parts[0])
        if len(parts) > 1:
            result["total_tracks"] = _to_int(parts[1])
    result["total_tracks"] = result["total_tracks"] or _to_int(_get_tag(tags, "totaltracks", "tracktotal"))

    result["disc_no"] = _to_int(_get_tag(tags, "discnumber"))

    date = _get_tag(tags, "date", "year")
    if date:
        result["year"] = _to_int(str(date)[:4])
        if len(str(date)) >= 10:
            result["release_date"] = str(date)[:10]

    lyrics = _get_tag(tags, "lyrics", "unsyncedlyrics")
    if lyrics:
        result["lyrics"] = lyrics
        result["has_lyrics"] = True

    result["has_cover"] = len(audio.pictures) > 0
    result["tag_version"] = "Vorbis"
    result["comment"] = _get_tag(tags, "comment")


def _read_m4a(audio, result: dict):
    tags = audio.tags
    if not tags:
        return

    result["title"] = _get_tag(tags, "\xa9nam")
    result["artist"] = _get_tag(tags, "\xa9ART")
    result["album_artist"] = _get_tag(tags, "aART")
    result["album_title"] = _get_tag(tags, "\xa9alb")
    result["genre"] = _get_tag(tags, "\xa9gen")
    result["label"] = _get_tag(tags, "\xa9pub", "----:com.apple.iTunes:LABEL")
    result["isrc"] = _get_tag(tags, "----:com.apple.iTunes:ISRC")

    trkn = tags.get("trkn")
    if trkn and trkn[0]:
        pair = trkn[0]
        if isinstance(pair, (list, tuple)):
            result["track_no"] = pair[0] if pair[0] else None
            result["total_tracks"] = pair[1] if len(pair) > 1 and pair[1] else None
        else:
            result["track_no"] = _to_int(pair)

    disk = tags.get("disk")
    if disk and disk[0]:
        result["disc_no"] = disk[0][0] if isinstance(disk[0], (list, tuple)) else _to_int(disk[0])

    year_tag = _get_tag(tags, "\xa9day")
    if year_tag:
        s = str(year_tag).strip()
        result["year"] = _to_int(s[:4])
        if len(s) >= 10:
            result["release_date"] = s[:10]

    lyrics = _get_tag(tags, "\xa9lyr")
    if lyrics:
        result["lyrics"] = lyrics
        result["has_lyrics"] = True

    result["has_cover"] = "covr" in tags
    result["tag_version"] = "iTunes"
    result["comment"] = _get_tag(tags, "\xa9cmt")


def _read_ogg(audio, result: dict):
    tags = audio
    result["title"] = _get_tag(tags, "title")
    result["artist"] = _get_tag(tags, "artist")
    result["album_artist"] = _get_tag(tags, "albumartist", "album artist")
    result["album_title"] = _get_tag(tags, "album")
    result["genre"] = _get_tag(tags, "genre")
    result["label"] = _get_tag(tags, "organization", "label", "publisher")
    result["isrc"] = _get_tag(tags, "isrc")

    trck = _get_tag(tags, "tracknumber")
    if trck:
        parts = str(trck).split("/")
        result["track_no"] = _to_int(parts[0])
        if len(parts) > 1:
            result["total_tracks"] = _to_int(parts[1])
    result["total_tracks"] = result["total_tracks"] or _to_int(_get_tag(tags, "totaltracks", "tracktotal"))

    result["disc_no"] = _to_int(_get_tag(tags, "discnumber"))

    date = _get_tag(tags, "date", "year")
    if date:
        result["year"] = _to_int(str(date)[:4])
        if len(str(date)) >= 10:
            result["release_date"] = str(date)[:10]

    lyrics = _get_tag(tags, "lyrics", "unsyncedlyrics")
    if lyrics:
        result["lyrics"] = lyrics
        result["has_lyrics"] = True

    result["has_cover"] = bool(tags.get("metadata_block_picture"))
    result["tag_version"] = "Vorbis"
    result["comment"] = _get_tag(tags, "comment")
