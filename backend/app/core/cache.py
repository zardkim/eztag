"""
인메모리 TTL 캐시 — browse API 응답 캐싱.

캐시 종류:
  files     : /api/browse/files      — 폴더별 파일 목록
  covers    : /api/browse/covers     — 파일별 커버 메타 목록
  children  : /api/browse/children   — 폴더별 하위 디렉터리
  roots     : /api/browse/roots      — 루트 폴더 목록
  cover_data: /api/browse/file-cover — 커버 원본 바이너리

무효화:
  - write-tags / batch-write-tags  → invalidate_path(path)
  - scan 완료                       → clear_all()

── 용량 상한 ────────────────────────────────────────────────
예전에는 maxsize 가 **항목 수**였다. 항목 하나의 크기와 무관해서,
하위 폴더 5,000개(응답 709KB)나 파일 1,000개(응답 2.6MB) 같은 큰 폴더를
여러 개 돌아다니면 최악의 경우 GB 단위까지 커질 수 있었다.
Synology DS220j 는 RAM 이 512MB 뿐이다.

지금은 `getsizeof` 로 **바이트 상한**을 건다. 총합은 CACHE_MEMORY_MB
환경변수로 조절한다(기본 128MB). 저사양 NAS 면 64 정도로 낮추면 된다.
"""
import os
import threading
from cachetools import TTLCache

_lock = threading.Lock()

_TOTAL_MB = max(16, int(os.getenv("CACHE_MEMORY_MB", "128")))
_MB = 1024 * 1024


def _sizeof_repr(value) -> int:
    """JSON 직렬화 가능한 값의 대략적 바이트 수. set 시 1회만 계산된다."""
    try:
        return len(repr(value))
    except Exception:
        return 1


def _sizeof_cover(value) -> int:
    """(data, mime, etag) 튜플 — 실제 바이너리 길이가 지배적이다."""
    try:
        return len(value[0]) + 64
    except Exception:
        return 1


# 총 예산 배분 (files 가 가장 크고, cover_data 는 바이너리라 별도로 묶는다)
_files_cache      = TTLCache(maxsize=int(_TOTAL_MB * 0.40) * _MB, ttl=900, getsizeof=_sizeof_repr)
_children_cache   = TTLCache(maxsize=int(_TOTAL_MB * 0.15) * _MB, ttl=600, getsizeof=_sizeof_repr)
_covers_cache     = TTLCache(maxsize=int(_TOTAL_MB * 0.05) * _MB, ttl=600, getsizeof=_sizeof_repr)
_cover_data_cache = TTLCache(maxsize=int(_TOTAL_MB * 0.40) * _MB, ttl=600, getsizeof=_sizeof_cover)
_roots_cache      = TTLCache(maxsize=1, ttl=600)   # 항목 1개뿐이라 개수 기준 유지


def _safe_set(cache: TTLCache, key, value) -> None:
    """단일 항목이 상한보다 크면 cachetools 가 ValueError 를 낸다 → 캐싱만 생략."""
    try:
        cache[key] = value
    except ValueError:
        pass


# ── files ────────────────────────────────────────────────────
def get_files(folder_path: str):
    with _lock:
        return _files_cache.get(folder_path)

def set_files(folder_path: str, value):
    with _lock:
        _safe_set(_files_cache, folder_path, value)

def invalidate_files(folder_path: str):
    with _lock:
        _files_cache.pop(folder_path, None)


# ── covers ───────────────────────────────────────────────────
def get_covers(file_path: str):
    with _lock:
        return _covers_cache.get(file_path)

def set_covers(file_path: str, value):
    with _lock:
        _safe_set(_covers_cache, file_path, value)

def invalidate_covers(file_path: str):
    with _lock:
        _covers_cache.pop(file_path, None)


# ── children ─────────────────────────────────────────────────
def get_children(folder_path: str):
    with _lock:
        return _children_cache.get(folder_path)

def set_children(folder_path: str, value):
    with _lock:
        _safe_set(_children_cache, folder_path, value)

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
        _safe_set(_cover_data_cache, key, value)

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


# ── 진단 ─────────────────────────────────────────────────────
def stats() -> dict:
    """캐시별 사용량/상한 (바이트). 용량 문제 진단용."""
    with _lock:
        return {
            "budget_mb": _TOTAL_MB,
            "files":      {"used": _files_cache.currsize,      "max": _files_cache.maxsize,      "items": len(_files_cache)},
            "children":   {"used": _children_cache.currsize,   "max": _children_cache.maxsize,   "items": len(_children_cache)},
            "covers":     {"used": _covers_cache.currsize,     "max": _covers_cache.maxsize,     "items": len(_covers_cache)},
            "cover_data": {"used": _cover_data_cache.currsize, "max": _cover_data_cache.maxsize, "items": len(_cover_data_cache)},
        }
