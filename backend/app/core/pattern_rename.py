"""태그 기반 파일명 패턴 처리 유틸리티."""
import re

# 파일명에 사용 불가한 문자
INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')


def render_pattern(pattern: str, fields: dict) -> str:
    """
    %field% 변수를 실제 태그 값으로 치환.

    지원 변수:
      %title%, %artist%, %albumartist%, %album%, %track%, %totaltracks%,
      %disc%, %year%, %genre%, %publisher%,
      %_filename%, %_ext%, %_bitrate%, %_codec%
    """
    FIELD_MAP = {
        "title": "title",
        "artist": "artist",
        "albumartist": "album_artist",
        "album": "album_title",
        "totaltracks": "total_tracks",
        "disc": "disc_no",
        "year": "year",
        "genre": "genre",
        "publisher": "label",
    }

    def _replace(m):
        var = m.group(1).lower()
        # 특수 파일 속성 변수
        if var in ("_filename", "_ext", "_bitrate", "_codec"):
            return str(fields.get(var) or "")
        # track: 2자리 제로패딩
        if var == "track":
            val = fields.get("track_no")
            if val is None:
                return ""
            try:
                return str(int(val)).zfill(2)
            except (ValueError, TypeError):
                return str(val)
        # disc: 패딩 없음
        if var == "disc":
            val = fields.get("disc_no")
            if val is None or val == 0:
                return ""
            return str(val)
        # 일반 태그 변수
        db_field = FIELD_MAP.get(var)
        if db_field:
            val = fields.get(db_field)
            return str(val) if val is not None else ""
        return m.group(0)  # 알 수 없는 변수는 그대로

    result = re.sub(r"%([^%]+)%", _replace, pattern)
    return result


def sanitize_filename(name: str) -> str:
    """
    파일명 안전 처리:
    - 금지 문자 → '_' 치환
    - 연속 공백 → 단일 공백
    - 앞뒤 공백/점 제거
    - 빈 문자열 → '_'
    """
    name = INVALID_CHARS.sub("_", name)
    name = re.sub(r" {2,}", " ", name)
    name = name.strip(" .")
    if not name:
        name = "_"
    return name


def build_new_name(pattern: str, file_info: dict, extension: str) -> str:
    """패턴 + 파일 정보 → 최종 새 파일명 (확장자 포함)."""
    name = render_pattern(pattern, file_info)
    name = sanitize_filename(name)
    ext = extension.lstrip(".")
    # 255바이트 제한
    max_bytes = 255 - len(f".{ext}".encode("utf-8"))
    encoded = name.encode("utf-8")
    if len(encoded) > max_bytes:
        name = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return f"{name}.{ext}"
