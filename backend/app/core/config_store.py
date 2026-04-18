"""DB 기반 앱 설정 읽기/쓰기 헬퍼."""
import json
import os
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from app.models.app_config import AppConfig

# (기본값, 설명)
DEFAULTS: dict[str, tuple] = {
    # 일반
    "site_name": ("eztag", "사이트 이름 (UI에 표시되는 앱 이름)"),
    "browser_title": ("eztag", "브라우저 탭에 표시되는 타이틀"),
    "scan_interval_minutes": ("0", "자동 스캔 주기 (분). 0=비활성화"),
    "extract_covers": ("true", "커버아트 자동 추출 여부"),
    "supported_formats": (".mp3,.flac,.m4a,.ogg,.aac", "지원 파일 포맷 (콤마 구분)"),
    "app_language": ("ko", "앱 언어 (ko/en)"),
    "cover_size": ("500", "커버 이미지 최대 크기 (px)"),
    "cleanup_on_scan": ("false", "스캔 시 누락 파일 자동 정리"),
    "destination_folders": ('[{"path":"/volume1/music","label":"NAS Music"}]', "이동 대상 폴더 목록 (JSON: [{path, label}])"),
    "startup_folder": ("workspace", "앱 시작 시 자동으로 열 폴더 (workspace/library/none)"),
    # recent_folders: 사용자별 개인 설정으로 이동 (user_preferences 테이블)
    "workspace_path": ("../data/workspace", "워크스페이스 폴더 경로 (환경변수 WORKSPACE_PATH 설정 시 무시됨)"),
    "library_path": ("../data/library", "라이브러리 폴더 경로 (환경변수 MUSIC_BASE_PATH 설정 시 무시됨)"),
    "lrc_base_folder": ("", "Get LRC 기본 폴더 경로"),
    "excluded_folders": ("@eaDir,.dav,@Recycle,#recycle,.Spotlight-V100,.Trashes", "파일 목록에서 제외할 폴더명 목록 (콤마 구분)"),
    "lrc_primary_source": ("alsong", "LRC 기본 소스 (alsong/bugs/lrclib)"),
    "lrc_fallback_source": ("bugs", "LRC 보조 소스 (alsong/bugs/lrclib/none)"),
    # Spotify (필수)
    "spotify_client_id": ("", "Spotify API Client ID"),
    "spotify_client_secret": ("", "Spotify API Client Secret"),
    "spotify_enabled": ("true", "Spotify 메타데이터 검색 활성화"),
    # 선택 메타데이터 소스
    "apple_music_enabled": ("false", "Apple Music 메타데이터 검색 활성화"),
    "apple_music_storefront": ("kr", "Apple Music 국가 코드 (kr/us/jp 등)"),
    "apple_music_classical_enabled": ("false", "Apple Music Classical 메타데이터 검색 활성화"),
    "apple_music_classical_storefront": ("us", "Apple Music Classical 국가 코드 (us/gb/de 등)"),
    "melon_enabled": ("true", "Melon 메타데이터 검색 활성화"),
    "bugs_enabled": ("true", "Bugs 메타데이터 검색 활성화"),
    # YouTube MV 검색
    "youtube_enabled": ("false", "YouTube 뮤직비디오 자동 검색 활성화"),
    "youtube_api_key": ("", "YouTube Data API v3 키"),
    # 마법사
    "wizard_presets": ("[]", "마법사 프리셋 목록 (JSON)"),
    # AI 커버아트 생성 (개발 중단)
    # "ai_cover_enabled": ("false", "AI 커버아트 생성 기능 활성화"),
    # "ai_cover_gemini_api_key": ("", "Google AI Studio API 키"),
    # "ai_cover_default_model": ("gemini-2.5-flash-image", "기본 Gemini 이미지 생성 모델"),
}


def get_config(db: Session, key: str) -> Optional[str]:
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    if row:
        return row.value
    return DEFAULTS.get(key, (None,))[0]


def get_all_config(db: Session) -> dict:
    rows = {r.key: r.value for r in db.query(AppConfig).all()}
    result = {}
    for key, (default, desc) in DEFAULTS.items():
        result[key] = {
            "value": rows.get(key, default),
            "default": default,
            "description": desc,
        }
    return result


def set_config(db: Session, key: str, value: str) -> AppConfig:
    if key not in DEFAULTS:
        raise ValueError(f"Unknown config key: {key}")
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    if row:
        row.value = value
    else:
        row = AppConfig(key=key, value=value, description=DEFAULTS[key][1])
        db.add(row)
    db.commit()
    return row


def set_bulk_config(db: Session, data: dict):
    for key, value in data.items():
        set_config(db, key, str(value))


def seed_defaults(db: Session) -> None:
    """DB에 없는 설정 기본값을 초기화 (첫 설치 또는 신규 키 추가 시)."""
    existing = {r.key for r in db.query(AppConfig).all()}
    added = []
    for key, (default, desc) in DEFAULTS.items():
        if key not in existing:
            db.add(AppConfig(key=key, value=default, description=desc))
            added.append(key)
    if added:
        db.commit()


def get_supported_formats(db: Session) -> set[str]:
    raw = get_config(db, "supported_formats") or ".mp3,.flac,.m4a,.ogg,.aac"
    return {ext.strip() for ext in raw.split(",") if ext.strip()}


def is_extract_covers(db: Session) -> bool:
    return get_config(db, "extract_covers") == "true"


def is_cleanup_on_scan(db: Session) -> bool:
    return get_config(db, "cleanup_on_scan") == "true"


def get_destination_folders(db: Session) -> list:
    """이동 대상 폴더 목록 반환. 각 항목: {path: str, label: str}"""
    raw = get_config(db, "destination_folders") or "[]"
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []


def set_destination_folders(db: Session, folders: list) -> None:
    """이동 대상 폴더 목록 저장."""
    set_config(db, "destination_folders", json.dumps(folders, ensure_ascii=False))


def get_workspace_path(db: Session) -> Path:
    """워크스페이스 경로 반환. 환경변수(WORKSPACE_PATH) > DB 설정 순."""
    env_val = os.getenv("WORKSPACE_PATH", "")
    if env_val:
        return Path(env_val).resolve()
    db_val = get_config(db, "workspace_path") or ""
    if db_val:
        return Path(db_val).resolve()
    return Path("/workspace").resolve()


def get_excluded_folders(db: Session) -> set[str]:
    """제외 폴더명 집합 반환."""
    raw = get_config(db, "excluded_folders") or ""
    return {name.strip() for name in raw.split(",") if name.strip()}


def get_library_path(db: Session) -> Path:
    """라이브러리 경로 반환. 환경변수(MUSIC_BASE_PATH) > DB 설정 순."""
    env_val = os.getenv("MUSIC_BASE_PATH", "")
    if env_val:
        return Path(env_val).resolve()
    db_val = get_config(db, "library_path") or ""
    if db_val:
        return Path(db_val).resolve()
    return Path("/music").resolve()
