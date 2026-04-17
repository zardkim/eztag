"""태그 기반 파일명 패턴 처리 유틸리티."""
import re
import unicodedata

# 파일명에 사용 불가한 문자 (ASCII 금지 문자 + 전각 대응 문자 + Division Slash 계열)
INVALID_CHARS = re.compile(
    r'[\\/:*?"<>|'
    r'\uff0a'   # ＊ Fullwidth Asterisk
    r'\uff0f'   # ／ Fullwidth Solidus
    r'\uff1a'   # ： Fullwidth Colon
    r'\uff1c'   # ＜ Fullwidth Less-Than
    r'\uff1e'   # ＞ Fullwidth Greater-Than
    r'\uff1f'   # ？ Fullwidth Question Mark
    r'\uff3c'   # ＼ Fullwidth Reverse Solidus
    r'\u2215'   # ∕ Division Slash
    r'\u2216'   # ∖ Set Minus
    r'\u29f5'   # ⧵ Reverse Solidus Operator
    r']'
)

_FIELD_MAP = {
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


def _resolve_var(var: str, fields: dict) -> str:
    """단일 변수명(%없이)을 값으로 변환."""
    var = var.lower()
    if var in ("_filename", "_ext", "_bitrate", "_codec"):
        return str(fields.get(var) or "")
    if var == "track":
        val = fields.get("track_no")
        if val is None:
            return ""
        try:
            return str(int(val))
        except (ValueError, TypeError):
            return str(val)
    if var == "disc":
        val = fields.get("disc_no")
        if val is None or val == 0:
            return ""
        return str(val)
    db_field = _FIELD_MAP.get(var)
    if db_field:
        val = fields.get(db_field)
        return str(val) if val is not None else ""
    return ""


def render_pattern(pattern: str, fields: dict) -> str:
    """
    패턴 변수를 실제 태그 값으로 치환.

    지원 변수:
      %title%, %artist%, %albumartist%, %album%, %track%, %totaltracks%,
      %disc%, %year%, %genre%, %publisher%,
      %_filename%, %_ext%, %_bitrate%, %_codec%

    지원 함수:
      $num(%field%,N) → 필드 값을 N자리 제로패딩 (예: $num(%track%,2), $num(%track%,3))
    """
    # 1단계: $num(%field%,N) 처리
    def _num_replace(m):
        inner_var = m.group(1)[1:-1]  # %track% → track
        digits = int(m.group(2))
        raw = _resolve_var(inner_var, fields)
        try:
            return str(int(raw)).zfill(digits)
        except (ValueError, TypeError):
            return raw

    pattern = re.sub(r'\$num\((%[^%]+%)\s*,\s*(\d+)\)', _num_replace, pattern)

    # 2단계: 나머지 %field% 처리 (%track%은 기본 2자리 패딩)
    def _replace(m):
        var = m.group(1).lower()
        if var == "track":
            raw = _resolve_var(var, fields)
            if not raw:
                return ""
            try:
                return str(int(raw)).zfill(2)
            except (ValueError, TypeError):
                return raw
        return _resolve_var(var, fields) or m.group(0)

    return re.sub(r"%([^%]+)%", _replace, pattern)


def sanitize_filename(name: str) -> str:
    """
    파일명 안전 처리:
    - NFC 유니코드 정규화 (macOS NFD 대응)
    - 제어 문자(0x00-0x1F, 0x7F) 제거
    - 금지 문자(\\/:*?"<>| 및 전각 대응 문자) → '_' 치환
    - 연속 공백 → 단일 공백
    - 앞뒤 공백/점 제거
    - 빈 문자열 → '_'
    """
    name = unicodedata.normalize("NFC", name)
    name = re.sub(r'[\x00-\x1f\x7f]', '', name)
    name = INVALID_CHARS.sub("_", name)
    name = re.sub(r" {2,}", " ", name)
    name = name.strip(" .")
    if not name:
        name = "_"
    return name


def sanitize_foldername(name: str) -> str:
    """
    폴더명 안전 처리:
    - 제어 문자(0x00-0x1F, 0x7F) 제거
    - 금지 문자(\\/:*?"<>|) → '_' 치환
    - 연속 공백 → 단일 공백
    - 앞뒤 공백/마침표 제거 (Windows 호환)
    - 빈 문자열 → '_'
    """
    name = re.sub(r'[\x00-\x1f\x7f]', '', name)
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
