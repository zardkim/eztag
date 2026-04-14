"""CUE 시트 파서 — CUE+FLAC 파일의 트랙 정보를 추출한다."""
from __future__ import annotations

import logging
import re
from pathlib import Path

_log = logging.getLogger(__name__)

# CUE 가상 트랙 경로 구분자
CUE_SEP = "::CUE::"


def _parse_index_time(time_str: str) -> float:
    """MM:SS:FF → 초 변환 (FF = 1/75 프레임)."""
    parts = time_str.strip().split(":")
    if len(parts) != 3:
        return 0.0
    mm, ss, ff = int(parts[0]), int(parts[1]), int(parts[2])
    return mm * 60 + ss + ff / 75.0


def _get_flac_duration(flac_path: Path) -> float | None:
    """mutagen으로 FLAC 총 재생시간(초) 반환."""
    try:
        import mutagen.flac
        f = mutagen.flac.FLAC(str(flac_path))
        return f.info.length
    except Exception:
        try:
            import mutagen
            f = mutagen.File(str(flac_path))
            if f and hasattr(f, "info") and hasattr(f.info, "length"):
                return f.info.length
        except Exception:
            pass
    return None


def _get_flac_meta(flac_path: Path) -> dict:
    """FLAC 파일에서 오디오 메타(sample_rate, bits_per_sample, bitrate) 추출."""
    meta = {}
    try:
        import mutagen.flac
        f = mutagen.flac.FLAC(str(flac_path))
        meta["sample_rate"] = f.info.sample_rate
        meta["bits_per_sample"] = getattr(f.info, "bits_per_sample", None)
        # FLAC bitrate 추정 (file_size / duration * 8 / 1000)
        duration = f.info.length
        if duration > 0:
            size = flac_path.stat().st_size
            meta["bitrate"] = int(size * 8 / duration / 1000)
    except Exception:
        pass
    return meta


def _decode_line(line: bytes | str) -> str:
    """CUE 파일 라인 디코딩 (UTF-8 BOM 처리 포함)."""
    if isinstance(line, bytes):
        for enc in ("utf-8-sig", "utf-8", "euc-kr", "cp949"):
            try:
                return line.decode(enc)
            except UnicodeDecodeError:
                continue
        return line.decode("latin-1")
    return line


def parse_cue_file(cue_path: Path) -> list[dict]:
    """
    CUE 파일을 파싱하여 트랙 정보 목록을 반환한다.

    반환 형식: [
      {
        "path": "/원본/파일.flac::CUE::01",  # 가상 경로
        "flac_path": "/원본/파일.flac",
        "track_no": 1,
        "title": "트랙 제목",
        "artist": "아티스트",
        "album_title": "앨범명",
        "album_artist": "앨범 아티스트",
        "genre": "...",
        "year": "2000",
        "disc_no": None,
        "duration": 180.5,
        "start_time": 0.0,
        "sample_rate": 44100,
        "bitrate": 900,
        "file_format": "FLAC",
        "is_cue_track": True,
      }, ...
    ]
    """
    try:
        raw = cue_path.read_bytes()
        # 인코딩 감지 (BOM 또는 heuristic)
        for enc in ("utf-8-sig", "utf-8", "euc-kr", "cp949"):
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = raw.decode("latin-1")
    except Exception as e:
        _log.warning(f"CUE 파일 읽기 실패: {cue_path}: {e}")
        return []

    lines = text.splitlines()

    # 전역 정보
    album_title = ""
    album_artist = ""
    genre = ""
    year = ""
    flac_filename = ""

    # 트랙별 정보 수집
    tracks: list[dict] = []
    current: dict | None = None

    for line in lines:
        line = line.strip()

        # FILE 선언 — 페어링 대상 오디오 파일
        m = re.match(r'FILE\s+"(.+?)"\s+', line, re.IGNORECASE)
        if m:
            flac_filename = m.group(1)
            continue

        # 전역 PERFORMER / TITLE
        if current is None:
            m = re.match(r'PERFORMER\s+"(.+?)"', line, re.IGNORECASE)
            if m:
                album_artist = m.group(1)
                continue
            m = re.match(r'TITLE\s+"(.+?)"', line, re.IGNORECASE)
            if m:
                album_title = m.group(1)
                continue
            m = re.match(r'REM\s+GENRE\s+(.+)', line, re.IGNORECASE)
            if m:
                genre = m.group(1).strip('"')
                continue
            m = re.match(r'REM\s+DATE\s+(.+)', line, re.IGNORECASE)
            if m:
                year = m.group(1).strip('"')
                continue

        # TRACK 시작
        m = re.match(r'TRACK\s+(\d+)\s+AUDIO', line, re.IGNORECASE)
        if m:
            if current:
                tracks.append(current)
            current = {
                "track_no": int(m.group(1)),
                "title": "",
                "artist": album_artist,
                "index01": None,
            }
            continue

        if current is None:
            continue

        # 트랙 내 TITLE
        m = re.match(r'TITLE\s+"(.+?)"', line, re.IGNORECASE)
        if m:
            current["title"] = m.group(1)
            continue

        # 트랙 내 PERFORMER
        m = re.match(r'PERFORMER\s+"(.+?)"', line, re.IGNORECASE)
        if m:
            current["artist"] = m.group(1)
            continue

        # INDEX 01 — 실제 트랙 시작 시간
        m = re.match(r'INDEX\s+01\s+(\d+:\d+:\d+)', line, re.IGNORECASE)
        if m:
            current["index01"] = _parse_index_time(m.group(1))
            continue

    if current:
        tracks.append(current)

    if not tracks:
        return []

    # 페어링 FLAC 파일 경로 확인
    flac_path = cue_path.parent / flac_filename
    if not flac_path.exists():
        # 파일명 대소문자 무시 탐색
        for f in cue_path.parent.iterdir():
            if f.name.lower() == flac_filename.lower():
                flac_path = f
                break
        else:
            _log.warning(f"CUE 페어링 파일 없음: {flac_filename}")
            return []

    total_duration = _get_flac_duration(flac_path)
    audio_meta = _get_flac_meta(flac_path)
    flac_stat = flac_path.stat()
    ext = flac_path.suffix.lstrip(".").upper()

    result = []
    for i, t in enumerate(tracks):
        start = t.get("index01") or 0.0
        if i + 1 < len(tracks):
            next_start = tracks[i + 1].get("index01") or start
            duration = max(0.0, next_start - start)
        elif total_duration is not None:
            duration = max(0.0, total_duration - start)
        else:
            duration = None

        result.append({
            "id": None,
            "album_id": None,
            "filename": flac_path.name,
            "path": f"{flac_path}{CUE_SEP}{t['track_no']:02d}",
            "flac_path": str(flac_path),
            "title": t["title"] or flac_path.stem,
            "artist": t["artist"],
            "album_artist": album_artist,
            "album_title": album_title,
            "track_no": t["track_no"],
            "total_tracks": len(tracks),
            "disc_no": None,
            "year": int(year) if year.isdigit() else None,
            "release_date": None,
            "genre": genre or None,
            "label": None,
            "isrc": None,
            "duration": round(duration, 2) if duration is not None else None,
            "start_time": round(start, 2),
            "bitrate": audio_meta.get("bitrate"),
            "sample_rate": audio_meta.get("sample_rate"),
            "bits_per_sample": audio_meta.get("bits_per_sample"),
            "tag_version": None,
            "comment": None,
            "file_format": ext,
            "has_cover": (cue_path.parent / "cover.jpg").exists()
                         or (cue_path.parent / "cover.png").exists()
                         or any(cue_path.parent.glob("*.jpg"))
                         or any(cue_path.parent.glob("*.png")),
            "has_lyrics": False,
            "is_title_track": False,
            "youtube_url": None,
            "has_lrc": False,
            "lyrics": None,
            "file_size": flac_stat.st_size,
            "modified_time": flac_stat.st_mtime,
            "scanned": True,
            "is_cue_track": True,
        })

    return result
