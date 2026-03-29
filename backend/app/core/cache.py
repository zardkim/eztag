"""
인메모리 TTL 캐시 — browse API 응답 캐싱.

캐시 종류:
  files    : /api/browse/files   — 폴더별 파일 목록 (TTL 3분)
  covers   : /api/browse/covers  — 파일별 커버 목록 (TTL 10분)
  children : /api/browse/children — 폴더별 하위 디렉터리 (TTL 5분)
  roots    : /api/browse/roots   — 루트 폴더 목록 (TTL 5분)

무효화:
  - write-tags / batch-write-tags  → invalidate_path(path)
  - scan 완료                       → clear_all()
"""
import threading
from cachetools import TTLCache

_lock = threading.Lock()

_files_cache      = TTLCache(maxsize=500,  ttl=900)   # 폴더 500개, 15분
_covers_cache     = TTLCache(maxsize=2000, ttl=600)   # 파일 2000개, 10분
_children_cache   = TTLCache(maxsize=500,  ttl=600)   # 폴더 500개, 10분
_roots_cache      = TTLCache(maxsize=1,    ttl=600)   # 루트 1개,   10분
_cover_data_cache = TTLCache(maxsize=500,  ttl=600)   # 커버 바이너리 500개, 10분 (동시 요청 DB 충돌 방지)


# ── files ────────────────────────────────────────────────────
def get_files(folder_path: str):
    with _lock:
        return _files_cache.get(folder_path)

def set_files(folder_path: str, value):
    with _lock:
        _files_cache[folder_path] = value

def invalidate_files(folder_path: str):
    with _lock:
        _files_cache.pop(folder_path, None)


# ── covers ───────────────────────────────────────────────────
def get_covers(file_path: str):
    with _lock:
        return _covers_cache.get(file_path)

def set_covers(file_path: str, value):
    with _lock:
        _covers_cache[file_path] = value

def invalidate_covers(file_path: str):
    with _lock:
        _covers_cache.pop(file_path, None)


# ── children ─────────────────────────────────────────────────
def get_children(folder_path: str):
    with _lock:
        return _children_cache.get(folder_path)

def set_children(folder_path: str, value):
    with _lock:
        _children_cache[folder_path] = value

def invalidate_children(folder_path: str):
    with _lock:
        _children_cache.pop(folder_path, None)


# ── roots ────────────────────────────────────────────────────
def get_roots():
    with _lock:
        return _roots_cache.get("roots")

def set_roots(value):
    with _lock:
        _roots_cache["roots"] = value

def invalidate_roots():
    with _lock:
        _roots_cache.pop("roots", None)


# ── cover binary data ────────────────────────────────────────
def get_cover_data(key: str):
    with _lock:
        return _cover_data_cache.get(key)

def set_cover_data(key: str, value):
    with _lock:
        _cover_data_cache[key] = value

def invalidate_cover_data(file_path: str):
    with _lock:
        # 해당 파일의 모든 index 항목 제거
        keys_to_del = [k for k in list(_cover_data_cache.keys()) if k.startswith(file_path + ":")]
        for k in keys_to_del:
            _cover_data_cache.pop(k, None)


# ── 전체 무효화 (스캔 완료 후) ────────────────────────────────
def clear_all():
    with _lock:
        _files_cache.clear()
        _covers_cache.clear()
        _children_cache.clear()
        _roots_cache.clear()
        _cover_data_cache.clear()


# ── 파일 쓰기 후 관련 캐시 제거 ──────────────────────────────
def invalidate_for_file(file_path: str):
    """태그 쓰기 후 해당 파일의 커버 캐시 + 부모 폴더의 파일 캐시 삭제."""
    from pathlib import Path
    folder = str(Path(file_path).parent)
    invalidate_files(folder)
    invalidate_covers(file_path)
    invalidate_cover_data(file_path)
