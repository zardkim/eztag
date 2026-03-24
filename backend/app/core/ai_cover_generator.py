"""Google Imagen 4 기반 AI 커버아트 생성."""
import base64
import io
import json
import logging
import uuid
from pathlib import Path

import requests
from PIL import Image

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# 분위기 프리셋 → 영문 키워드
MOOD_PRESETS: dict[str, str] = {
    "energetic": "energetic, powerful, dynamic, bold, intense",
    "emotional":  "emotional, soft, romantic, dreamy, tender",
    "retro":      "retro, vintage, nostalgic, film grain, analog",
    "kpop":       "k-pop aesthetic, colorful, trendy, idol, modern",
    "jazz":       "elegant, sophisticated, minimalist, timeless",
    "hiphop":     "urban, street, bold, raw, gritty",
    "drive":      "night city, neon lights, road, cinematic, moody",
    "healing":    "serene, nature, peaceful, soft light, watercolor",
    "dark":       "dark, dramatic, powerful, cinematic, edgy",
}

# 연도 범위 → 시대 스타일 키워드
YEAR_STYLES: list[tuple] = [
    ((0,    1979), "70s aesthetic, psychedelic, vinyl record era"),
    ((1980, 1989), "80s neon, synthwave, retro pop"),
    ((1990, 1999), "90s aesthetic, grunge, bright pop"),
    ((2000, 2009), "Y2K aesthetic, glossy, early digital"),
    ((2010, 2019), "modern, clean, contemporary"),
    ((2020, 9999), "current, trendy, minimalist digital"),
]

NEGATIVE_PROMPT = (
    "text, watermark, logo, album title, artist name, letters, numbers, "
    "blurry, low quality, distorted, deformed, oversaturated"
)

OUTPUT_SIZE = 500  # 최종 출력 크기 (px)


class AICoverGenerator:
    def __init__(self, api_key: str, covers_path: str):
        self.api_key = api_key
        self.preview_dir = Path(covers_path) / "ai_preview"
        self.preview_dir.mkdir(parents=True, exist_ok=True)

    # ── 분위기 자동 선택 ────────────────────────────────────────
    def auto_select_mood(self, track_info: dict, hint: str = "") -> str:
        """트랙 정보(폴더명, 앨범명, 아티스트, 장르, 힌트)를 분석해 MOOD_PRESETS 중 가장 적합한 키 반환."""
        mood_list = ", ".join(MOOD_PRESETS.keys())
        context_parts = []
        if track_info.get("folder_name"):
            context_parts.append(f"Folder: {track_info['folder_name']}")
        if track_info.get("album_title"):
            context_parts.append(f"Album: {track_info['album_title']}")
        if track_info.get("artist"):
            context_parts.append(f"Artist: {track_info['artist']}")
        if track_info.get("genre"):
            context_parts.append(f"Genre: {track_info['genre']}")
        if hint:
            context_parts.append(f"Keywords: {hint}")
        context = "; ".join(context_parts) or "unknown"

        url = f"{GEMINI_API_BASE}/models/gemini-2.0-flash:generateContent"
        payload = {
            "contents": [{
                "parts": [{"text": (
                    f"You are selecting a visual mood for an album cover art.\n"
                    f"Music info: {context}\n"
                    f"Choose exactly ONE mood from this list that best fits the music: {mood_list}\n"
                    f"Reply with only the single mood word, nothing else."
                )}]
            }]
        }
        try:
            resp = requests.post(
                url,
                json=payload,
                headers={"x-goog-api-key": self.api_key},
                timeout=15,
            )
            resp.raise_for_status()
            selected = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
            # 반환값이 유효한 preset 키인지 확인
            if selected in MOOD_PRESETS:
                return selected
            # 부분 매치 시도
            for key in MOOD_PRESETS:
                if key in selected:
                    return key
        except Exception as e:
            logger.warning(f"[ai_cover] auto_select_mood failed: {e}")
        return "energetic"  # 실패 시 기본값

    # ── 한국어 힌트 번역 ────────────────────────────────────────
    def translate_hint(self, hint_ko: str) -> str:
        """한국어 힌트 → 영문 이미지 프롬프트 키워드 (Gemini Flash)"""
        url = f"{GEMINI_API_BASE}/models/gemini-2.0-flash:generateContent"
        payload = {
            "contents": [{
                "parts": [{"text": (
                    "Translate this Korean description into English image prompt keywords "
                    "for album cover art generation. Output only keywords, comma-separated, "
                    "no explanation, no Korean.\n"
                    f"Korean: {hint_ko}"
                )}]
            }]
        }
        try:
            resp = requests.post(
                url,
                json=payload,
                headers={"x-goog-api-key": self.api_key},
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            logger.warning(f"[ai_cover] translate_hint failed: {e}")
            return hint_ko  # 실패 시 원문 그대로

    # ── 연도 스타일 ────────────────────────────────────────────
    @staticmethod
    def _year_style(year) -> str:
        if not year:
            return ""
        try:
            y = int(year)
        except (ValueError, TypeError):
            return ""
        for (start, end), style in YEAR_STYLES:
            if start <= y <= end:
                return style
        return ""

    # ── 프롬프트 조합 ──────────────────────────────────────────
    def build_prompt(self, track_info: dict, mood: str, hint_en: str = "") -> str:
        parts = ["Music album cover art."]

        album  = track_info.get("album_title") or track_info.get("folder_name", "")
        artist = track_info.get("artist") or track_info.get("album_artist", "")
        genre  = track_info.get("genre", "")
        year   = track_info.get("year")

        if album:  parts.append(f'Album: "{album}".')
        if artist: parts.append(f"Artist: {artist}.")
        if genre:  parts.append(f"Genre: {genre}.")
        if year:   parts.append(f"Year: {year}.")

        # auto: Gemini가 트랙 정보 기반으로 분위기 자동 선택
        if mood == "auto":
            mood = self.auto_select_mood(track_info, hint_en)

        mood_kw = MOOD_PRESETS.get(mood, "")
        if mood_kw:
            parts.append(f"Mood: {mood_kw}.")

        year_style = self._year_style(year)
        if year_style:
            parts.append(f"Era style: {year_style}.")

        if hint_en:
            parts.append(f"Additional atmosphere: {hint_en}.")

        parts.append(
            f"High quality square music album artwork, "
            f"no visible text, no watermarks, professional design."
        )
        return " ".join(parts)

    # ── 이미지 생성 (모델에 따라 자동 분기) ──────────────────────
    def generate(self, prompt: str, model: str = "gemini-2.5-flash-image") -> bytes:
        if model.startswith("gemini-"):
            return self._generate_gemini(prompt, model)
        else:
            return self._generate_imagen(prompt, model)

    # ── Gemini generateContent 방식 ────────────────────────────
    def _generate_gemini(self, prompt: str, model: str) -> bytes:
        """Gemini API(generateContent) → 500×500 JPEG bytes 반환"""
        url = f"{GEMINI_API_BASE}/models/{model}:generateContent"
        full_prompt = (
            f"{prompt} "
            f"Avoid: {NEGATIVE_PROMPT}."
        )
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
        }
        resp = requests.post(
            url,
            json=payload,
            headers={"x-goog-api-key": self.api_key},
            timeout=60,
        )
        if resp.status_code != 200:
            detail = resp.text
            try:
                detail = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                pass
            raise RuntimeError(f"Gemini API error {resp.status_code}: {detail}")

        candidates = resp.json().get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini API returned no candidates")

        for part in candidates[0].get("content", {}).get("parts", []):
            if "inlineData" in part:
                b64 = part["inlineData"].get("data", "")
                if b64:
                    raw = base64.b64decode(b64)
                    img = Image.open(io.BytesIO(raw)).convert("RGB")
                    img = img.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=92)
                    return buf.getvalue()

        raise RuntimeError("Gemini API returned no image data")

    # ── Imagen predict 방식 ────────────────────────────────────
    def _generate_imagen(self, prompt: str, model: str) -> bytes:
        """Imagen API(:predict) → 500×500 JPEG bytes 반환"""
        url = f"{GEMINI_API_BASE}/models/{model}:predict"
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "1:1",
                "negativePrompt": NEGATIVE_PROMPT,
            },
        }
        resp = requests.post(
            url,
            json=payload,
            headers={"x-goog-api-key": self.api_key},
            timeout=60,
        )
        if resp.status_code != 200:
            detail = resp.text
            try:
                detail = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                pass
            raise RuntimeError(f"Imagen API error {resp.status_code}: {detail}")

        predictions = resp.json().get("predictions", [])
        if not predictions:
            raise RuntimeError("Imagen API returned no images")

        b64 = predictions[0].get("bytesBase64Encoded", "")
        if not b64:
            raise RuntimeError("Imagen API returned empty image data")

        raw = base64.b64decode(b64)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        img = img.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=92)
        return buf.getvalue()

    # ── 미리보기 임시 저장 ─────────────────────────────────────
    def save_preview(self, image_bytes: bytes) -> str:
        gen_id = uuid.uuid4().hex
        (self.preview_dir / f"{gen_id}.jpg").write_bytes(image_bytes)
        return gen_id

    def preview_path(self, gen_id: str) -> Path:
        return self.preview_dir / f"{gen_id}.jpg"

    def preview_url(self, gen_id: str) -> str:
        return f"/covers/ai_preview/{gen_id}.jpg"

    def cleanup(self, gen_id: str):
        (self.preview_dir / f"{gen_id}.jpg").unlink(missing_ok=True)

    # ── 오래된 미리보기 일괄 정리 ─────────────────────────────
    def cleanup_expired(self, max_age_seconds: int = 3600):
        import time
        now = time.time()
        for f in self.preview_dir.glob("*.jpg"):
            try:
                if now - f.stat().st_mtime > max_age_seconds:
                    f.unlink()
            except Exception:
                pass
