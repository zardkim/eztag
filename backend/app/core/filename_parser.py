"""파일명 패턴 파싱 유틸리티 (browse.py, metadata.py 공용)."""
import re

_TAG_FROM_NAME_VARS = [
    "%title%", "%artist%", "%album_artist%", "%album%",
    "%track%", "%disc%", "%year%", "%genre%", "%label%",
]

_VAR_REGEX = {
    "%track%":        r"(\d+)",
    "%disc%":         r"(\d+)",
    "%year%":         r"(\d{4})",
    "%title%":        r"(.+?)",
    "%artist%":       r"(.+?)",
    "%album_artist%": r"(.+?)",
    "%album%":        r"(.+?)",
    "%genre%":        r"(.+?)",
    "%label%":        r"(.+?)",
}

_VAR_TO_FIELD = {
    "%title%":        "title",
    "%artist%":       "artist",
    "%album_artist%": "album_artist",
    "%album%":        "album_title",
    "%track%":        "track_no",
    "%disc%":         "disc_no",
    "%year%":         "year",
    "%genre%":        "genre",
    "%label%":        "label",
}

# 자동 감지 순서 (우선순위 높은 순)
DETECT_PRESETS = [
    "%track%-%artist%-%disc%-%title%",   # 멜론: 001-아티스트-01-제목
    "%disc%-%track% - %title%",          # 디스크-트랙 - 제목: 1-001 - 제목
    "%disc%-%track% %title%",            # 디스크-트랙 제목: 1-001 제목
    "%disc%-%track%-%title%",            # 디스크-트랙-제목: 1-001-제목
    "%track% - %artist% - %title%",      # 트랙 - 아티스트 - 제목 (공백)
    "%track%-%artist%-%title%",          # 트랙-아티스트-제목 (공백 없음)
    "%artist% - %title%",               # 아티스트 - 제목 (공백)
    "%track% - %title%",                # 트랙 - 제목 (공백)
    "%track% %title%",                  # 트랙 제목: 001 제목
    "%track%-%title%",                  # 트랙-제목 (공백 없음)
]


def pattern_to_regex(pattern: str):
    """패턴 문자열 → (컴파일된 정규식, 필드목록) 반환."""
    fields = []
    regex_str = ""
    i = 0
    while i < len(pattern):
        matched = False
        for var in _TAG_FROM_NAME_VARS:
            if pattern[i:].startswith(var):
                regex_str += _VAR_REGEX[var]
                fields.append(var)
                i += len(var)
                matched = True
                break
        if not matched:
            regex_str += re.escape(pattern[i])
            i += 1
    return re.compile(f"^{regex_str}$", re.IGNORECASE), fields


def parse_filename_by_pattern(filename: str, pattern: str) -> dict:
    """파일명을 패턴으로 파싱 → 태그 dict. 매칭 실패 시 {}."""
    rx, fields = pattern_to_regex(pattern)
    m = rx.match(filename)
    if not m:
        return {}
    result = {}
    for i, var in enumerate(fields):
        val = m.group(i + 1).strip()
        field = _VAR_TO_FIELD[var]
        if field in ("track_no", "disc_no", "year"):
            try:
                result[field] = int(val)
            except ValueError:
                result[field] = None
        else:
            result[field] = val
    return result


def detect_pattern(filenames: list) -> dict:
    """
    샘플 파일명에서 가장 잘 맞는 패턴 자동 감지.
    Returns: { pattern, confidence, matched, total }
    """
    if not filenames:
        return {"pattern": "%artist% - %title%", "confidence": 0.0, "matched": 0, "total": 0}

    sample = filenames[:20]
    best_pattern = None
    best_matched = -1

    for preset in DETECT_PRESETS:
        matched = sum(1 for fn in sample if parse_filename_by_pattern(fn, preset))
        if matched > best_matched:
            best_matched = matched
            best_pattern = preset

    confidence = round(best_matched / len(sample), 2) if sample else 0.0
    return {
        "pattern": best_pattern or "%artist% - %title%",
        "confidence": confidence,
        "matched": best_matched,
        "total": len(sample),
    }
