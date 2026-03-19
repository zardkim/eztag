"""
Extract and save cover art from audio files.
"""
import os
import hashlib
from pathlib import Path
from typing import Optional
from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4

# 로컬 커버 파일 우선순위 (낮은 인덱스 = 높은 우선순위)
_LOCAL_COVER_NAMES = ["cover", "folder", "front", "back", "front cover", "back cover"]
_LOCAL_COVER_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def find_local_cover(audio_file_path: str, covers_dir: str) -> Optional[str]:
    """
    오디오 파일과 같은 폴더에서 커버 이미지 파일을 탐색.
    cover > folder > front > back > front cover > back cover 순 우선순위.
    Returns relative path like "ab/abcdef1234.jpg" or None.
    """
    folder = Path(audio_file_path).parent

    try:
        dir_files = list(folder.iterdir())
    except Exception:
        return None

    # 폴더 내 파일을 {소문자 stem → Path} 매핑
    file_map: dict[str, Path] = {}
    for f in dir_files:
        if f.suffix.lower() in _LOCAL_COVER_EXTS:
            file_map[f.stem.lower()] = f

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

        img_ext = candidate.suffix.lower().lstrip(".")
        if img_ext == "jpeg":
            img_ext = "jpg"

        digest = hashlib.md5(data).hexdigest()
        subdir = digest[:2]
        filename = f"{digest}.{img_ext}"
        save_dir = Path(covers_dir) / subdir
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / filename
        if not save_path.exists():
            save_path.write_bytes(data)
        return f"{subdir}/{filename}"

    return None


def extract_cover(file_path: str, covers_dir: str) -> Optional[str]:
    """
    Extract cover art from audio file and save to covers_dir.
    Returns relative path like "ab/abcdef1234.jpg" or None.
    """
    path = Path(file_path)
    ext = path.suffix.lower().lstrip(".")

    try:
        data, mime = _get_cover_data(file_path, ext)
    except Exception:
        return None

    if not data:
        return None

    img_ext = "jpg" if "jpeg" in mime or "jpg" in mime else "png"
    digest = hashlib.md5(data).hexdigest()
    subdir = digest[:2]
    filename = f"{digest}.{img_ext}"

    save_dir = Path(covers_dir) / subdir
    save_dir.mkdir(parents=True, exist_ok=True)

    save_path = save_dir / filename
    if not save_path.exists():
        save_path.write_bytes(data)

    return f"{subdir}/{filename}"


def _get_cover_data(file_path: str, ext: str):
    if ext == "mp3":
        return _from_mp3(file_path)
    elif ext == "flac":
        return _from_flac(file_path)
    elif ext in ("m4a", "aac", "mp4"):
        return _from_m4a(file_path)
    elif ext == "ogg":
        return None, None
    return None, None


def _from_mp3(file_path: str):
    audio = MutagenFile(file_path, easy=False)
    if not audio or not audio.tags:
        return None, None
    for key in audio.tags.keys():
        if key.startswith("APIC"):
            apic = audio.tags[key]
            return apic.data, apic.mime
    return None, None


def _from_flac(file_path: str):
    audio = FLAC(file_path)
    if audio.pictures:
        pic = audio.pictures[0]
        return pic.data, pic.mime
    return None, None


def _from_m4a(file_path: str):
    audio = MP4(file_path)
    covr = audio.tags.get("covr") if audio.tags else None
    if covr:
        data = bytes(covr[0])
        mime = "image/jpeg" if covr[0].imageformat == 13 else "image/png"
        return data, mime
    return None, None
