"""AI 커버아트 생성 API (Google Imagen 4)."""
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.auth import get_current_user
from app.core.config_store import get_config
from app.core.tag_writer import write_cover
from app.core.ai_cover_generator import AICoverGenerator, MOOD_PRESETS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai-cover", tags=["ai-cover"])

COVERS_PATH_ENV = "/app/data/covers"


def _get_covers_path() -> str:
    import os
    return os.getenv("COVERS_PATH", COVERS_PATH_ENV)


def _get_generator(db: Session) -> AICoverGenerator:
    api_key = get_config(db, "ai_cover_gemini_api_key") or ""
    if not api_key:
        raise HTTPException(status_code=400, detail="ai_cover_not_configured")
    if get_config(db, "ai_cover_enabled") != "true":
        raise HTTPException(status_code=400, detail="ai_cover_disabled")
    return AICoverGenerator(api_key=api_key, covers_path=_get_covers_path())


# ── 단일 생성 ──────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    path: Optional[str] = None          # 오디오 파일 경로 (메타데이터 자동 읽기)
    folder_name: Optional[str] = None   # 폴더명 기반 생성 시
    album_title: Optional[str] = None
    artist: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    mood: str = "energetic"
    hint: Optional[str] = None          # 한국어 힌트 (자동 번역)
    model: str = "imagen-4.0-generate-001"


@router.post("/generate")
def generate_cover(
    req: GenerateRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    gen = _get_generator(db)

    # 오디오 파일에서 메타데이터 읽기
    track_info: dict = {
        "album_title": req.album_title or "",
        "artist":      req.artist or "",
        "genre":       req.genre or "",
        "year":        req.year,
        "folder_name": req.folder_name or "",
    }
    if req.path:
        try:
            from app.core.tag_reader import read_tags
            tags = read_tags(req.path)
            for k in ("title", "artist", "album_title", "album_artist", "genre", "year"):
                if tags.get(k) and not track_info.get(k):
                    track_info[k] = tags[k]
            if not track_info.get("folder_name"):
                track_info["folder_name"] = Path(req.path).parent.name
        except Exception as e:
            logger.warning(f"[ai_cover] tag read failed for {req.path}: {e}")

    # 한국어 힌트 번역
    hint_en = ""
    if req.hint:
        hint_en = gen.translate_hint(req.hint)

    # 프롬프트 생성 → 이미지 생성
    prompt = gen.build_prompt(track_info, req.mood, hint_en)
    model = get_config(db, "ai_cover_default_model") or req.model
    try:
        image_bytes = gen.generate(prompt, model=model)
    except RuntimeError as e:
        logger.error(f"[ai_cover] generate failed (model={model}): {e}")
        raise HTTPException(status_code=502, detail=str(e))

    gen_id = gen.save_preview(image_bytes)
    return {
        "generation_id": gen_id,
        "preview_url": gen.preview_url(gen_id),
        "prompt_used": prompt,
    }


# ── 단일 파일에 적용 ───────────────────────────────────────────

class ApplyRequest(BaseModel):
    path: str
    generation_id: str


@router.post("/apply")
def apply_cover(
    req: ApplyRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    gen = AICoverGenerator(api_key="", covers_path=_get_covers_path())
    preview = gen.preview_path(req.generation_id)
    if not preview.exists():
        raise HTTPException(status_code=404, detail="preview_not_found")

    image_bytes = preview.read_bytes()

    # 오디오 파일에 커버 임베드
    ok = write_cover(req.path, image_bytes, "image/jpeg", 3)
    if not ok:
        raise HTTPException(status_code=500, detail="write_cover_failed")

    # 폴더에 cover.jpg 저장
    try:
        cover_file = Path(req.path).parent / "cover.jpg"
        cover_file.write_bytes(image_bytes)
    except Exception as e:
        logger.warning(f"[ai_cover] cover.jpg save failed: {e}")

    # 캐시 무효화
    try:
        from app.core.file_cache import _cache
        _cache.invalidate_for_file(req.path)
    except Exception:
        pass

    gen.cleanup(req.generation_id)
    return {"success": True}


# ── 폴더 전체 파일에 동일 이미지 적용 ─────────────────────────

class ApplyFolderRequest(BaseModel):
    folder_path: str
    generation_id: str


@router.post("/apply-folder")
def apply_cover_folder(
    req: ApplyFolderRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    gen = AICoverGenerator(api_key="", covers_path=_get_covers_path())
    preview = gen.preview_path(req.generation_id)
    if not preview.exists():
        raise HTTPException(status_code=404, detail="preview_not_found")

    image_bytes = preview.read_bytes()
    folder = Path(req.folder_path)

    supported = {".mp3", ".flac", ".m4a", ".ogg", ".aac"}
    audio_files = [f for f in folder.iterdir() if f.suffix.lower() in supported]
    if not audio_files:
        raise HTTPException(status_code=400, detail="no_audio_files")

    applied = 0
    failed = 0
    for af in audio_files:
        try:
            ok = write_cover(str(af), image_bytes, "image/jpeg", 3)
            if ok:
                applied += 1
            else:
                failed += 1
        except Exception as e:
            logger.warning(f"[ai_cover] apply failed for {af}: {e}")
            failed += 1

    # 폴더에 cover.jpg 저장
    try:
        (folder / "cover.jpg").write_bytes(image_bytes)
    except Exception as e:
        logger.warning(f"[ai_cover] cover.jpg save failed: {e}")

    # 캐시 무효화
    try:
        from app.core.file_cache import _cache
        _cache.invalidate(str(folder))
    except Exception:
        pass

    gen.cleanup(req.generation_id)
    return {"applied": applied, "failed": failed}


# ── 미리보기 삭제 ──────────────────────────────────────────────

@router.delete("/preview/{generation_id}")
def delete_preview(
    generation_id: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    gen = AICoverGenerator(api_key="", covers_path=_get_covers_path())
    gen.cleanup(generation_id)
    return {"success": True}


# ── 분위기 프리셋 목록 ─────────────────────────────────────────

@router.get("/moods")
def get_moods(_=Depends(get_current_user)):
    return {"moods": ["auto"] + list(MOOD_PRESETS.keys())}
