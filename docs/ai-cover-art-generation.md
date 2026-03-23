# AI 커버아트 생성 기능 구현 계획서

> **버전**: 2.0
> **작성일**: 2026-03-23
> **대상 버전**: eztag v0.7.0
> **AI 제공자**: Google Gemini (Imagen 4)

---

## 1. 배경 및 목적

멜론/벅스 차트 모음, 운동 플레이리스트 등 인터넷에서 수집한 음악 파일은 앨범아트가 없는 경우가 많다. 기존에는 Google CSE, Spotify 등 외부 이미지를 가져오는 방식을 사용했지만, 검색 결과가 없거나 플레이리스트 성격의 컬렉션에는 적합하지 않다.

**Google Gemini API의 Imagen 4 모델**과 연동하여 트랙 메타데이터(아티스트, 앨범명, 장르, 연도)와 사용자가 지정한 분위기 키워드를 기반으로 어울리는 커버아트를 AI로 자동 생성하는 기능을 추가한다.

---

## 2. AI 모델 — Google Imagen 4

### 2.1 모델 선택

| 모델 ID | 특징 | 용도 |
|---------|------|------|
| `imagen-4.0-generate-001` | 표준, 균형잡힌 품질/속도 | **기본값** |
| `imagen-4.0-fast-generate-001` | 빠른 생성, 저비용 | 배치 일괄 생성 |
| `imagen-4.0-ultra-generate-001` | 최고 품질 | 단일 파일 정밀 생성 |

### 2.2 API 기본 정보

| 항목 | 값 |
|------|-----|
| 엔드포인트 | `https://generativelanguage.googleapis.com/v1beta/models/{model}:predict` |
| 인증 | Google AI Studio API Key (`x-goog-api-key` 헤더 또는 `?key=` 쿼리) |
| 출력 형식 | Base64 인코딩 이미지 (JPEG/PNG) |
| 지원 비율 | `1:1` (기본), `3:4`, `4:3`, `9:16`, `16:9` |
| 생성 크기 | `1K` (약 1024px), `2K` (약 2048px) |
| 출력 크기 | **500×500** (1K 생성 후 PIL로 리사이즈) |
| 프롬프트 언어 | **영어만 지원** → 한국어 힌트는 Gemini Flash로 번역 후 사용 |
| SynthID 워터마크 | 비가시적 워터마크 자동 삽입 (제거 불필요) |
| 비용 | ~$0.03/장 (표준), ~$0.01/장 (fast) |

### 2.3 REST API 요청/응답 형식

**요청**
```http
POST https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict
x-goog-api-key: {API_KEY}
Content-Type: application/json

{
  "instances": [
    { "prompt": "Album cover art for a 90s K-pop compilation. Vibrant neon colors, energetic, retro aesthetic. No text." }
  ],
  "parameters": {
    "sampleCount": 1,
    "aspectRatio": "1:1",
    "negativePrompt": "text, watermark, logo, blurry, low quality, distorted"
  }
}
```

**응답**
```json
{
  "predictions": [
    {
      "bytesBase64Encoded": "/9j/4AAQSkZJRgAB...",
      "mimeType": "image/jpeg"
    }
  ]
}
```

---

## 3. 사용 시나리오

### 시나리오 A — 단일 파일 커버 생성
1. 파일 브라우저에서 커버가 없는 파일 선택
2. TagPanel에서 "🎨 AI 커버 생성" 버튼 클릭
3. 트랙 정보(앨범명, 아티스트, 장르, 연도)가 자동으로 키워드에 반영됨
4. 분위기 프리셋 선택 + 추가 키워드(한국어 가능) 입력
5. 생성 → 미리보기 → 마음에 들면 파일에 즉시 임베드

### 시나리오 B — 폴더 일괄 생성 (플레이리스트)
1. 커버가 없는 파일들이 있는 폴더 오픈
2. 브라우저 툴바 "🎨 AI 일괄 생성" 버튼 클릭
3. 적용 모드 선택:
   - **폴더 단일**: 이미지 1장 생성 → 전체 파일에 동일 적용 (저비용)
   - **파일별 개별**: 각 트랙 메타데이터로 개별 생성
4. 분위기/키워드 설정 → 생성 → 미리보기 → 일괄 적용

### 시나리오 C — 앨범 대표 커버
1. AlbumDetail 페이지에서 커버 없는 앨범에 "🎨 AI 생성" 버튼
2. 앨범명, 아티스트, 장르, 연도 자동 반영
3. 생성 → 앨범 커버로 적용 (커버 파일 저장)

---

## 4. 프롬프트 설계

### 4.1 핵심 키워드 구조

사용자가 UI에서 입력/선택한 값을 조합하여 영문 프롬프트를 자동 구성한다.

```
[기본 형식]
Music album cover art.
Album: "{album_title}". Artist: {artist}. Genre: {genre}. Year: {year}.
Mood: {mood_keywords}.
Style: {style_preset_keywords}.
High quality square artwork, no visible text, no watermarks.
```

**예시 — 90년대 K-pop 차트 모음**
```
Music album cover art.
Album: "90s K-pop Hit Chart". Genre: K-pop. Year: 1995.
Mood: nostalgic, bright, cheerful, youthful energy.
Style: retro aesthetic, vivid colors, 90s pop culture.
High quality square artwork, no visible text, no watermarks.
```

**예시 — 운동 플레이리스트**
```
Music album cover art.
Album: "WorkOut Mix Vol.3". Genre: Electronic, Hip-hop.
Mood: energetic, powerful, motivating, intense.
Style: dynamic motion blur, bold neon colors, athletic.
High quality square artwork, no visible text, no watermarks.
```

### 4.2 분위기(Mood) 프리셋

사용자가 UI에서 선택하는 프리셋. 한국어 라벨 → 영문 프롬프트 키워드로 변환.

| UI 라벨 | 영문 키워드 | 적합한 상황 |
|---------|------------|------------|
| **에너지틱** | energetic, powerful, dynamic, bold, intense | 운동, 힙합, 댄스 |
| **감성/발라드** | emotional, soft, romantic, dreamy, tender | 발라드, 팝, 감성곡 |
| **레트로** | retro, vintage, nostalgic, film grain, analog | 7~90년대 모음 |
| **K-팝** | k-pop aesthetic, colorful, trendy, idol, modern | K-pop 차트 |
| **재즈/클래식** | elegant, sophisticated, minimalist, timeless | 재즈, 클래식 |
| **힙합/랩** | urban, street, bold typography feel, raw, gritty | 힙합, R&B |
| **드라이브/야경** | night city, neon lights, road, cinematic, moody | 드라이브 모음 |
| **자연/힐링** | serene, nature, peaceful, soft light, watercolor | 힐링, 명상 |
| **다크/록** | dark, dramatic, powerful, cinematic, edgy | 록, 메탈, 다크팝 |

### 4.3 연도(Year) 기반 자동 스타일 추가

트랙의 `year` 메타데이터를 읽어 시대적 스타일 키워드를 자동 추가한다.

| 연도 범위 | 자동 추가 키워드 |
|-----------|----------------|
| ~1979 | 70s aesthetic, psychedelic, vinyl record era |
| 1980~1989 | 80s neon, synthwave, retro pop |
| 1990~1999 | 90s aesthetic, grunge, bright pop |
| 2000~2009 | Y2K aesthetic, glossy, early digital |
| 2010~2019 | modern, clean, contemporary |
| 2020~ | current, trendy, minimalist digital |

### 4.4 한국어 힌트 처리 (2단계 방식)

Imagen 4는 영어 프롬프트만 지원하므로, 사용자가 한국어로 힌트를 입력하면 **Gemini Flash 텍스트 모델**로 먼저 영어로 변환 후 사용한다.

```
[사용자 입력] "새벽 드라이브, 약간 우울하지만 설레는 느낌"
      ↓  gemini-2.0-flash (translate to image prompt keywords)
[변환 결과] "late night drive, melancholic yet exciting, city lights, bittersweet atmosphere"
      ↓
[최종 프롬프트에 포함]
```

같은 API 키로 Gemini Flash 텍스트 생성도 가능하므로 추가 비용은 무시할 수 있는 수준 (입력 ~50토큰 = $0.00003).

### 4.5 네거티브 프롬프트 (고정)

```
text, watermark, logo, album title, artist name, letters, numbers,
blurry, low quality, distorted, deformed, oversaturated
```

---

## 5. 아키텍처 설계

### 5.1 전체 흐름

```
[프론트엔드]                    [백엔드]                 [Google AI]
    │                              │                         │
    │  POST /api/ai-cover/generate │                         │
    ├─────────────────────────────▶│                         │
    │  { path, mood, hint,         │  1. DB에서 트랙 메타데이터 조회
    │    year_auto, mode }         │  2. 한국어 힌트 → 영어 번역
    │                              │     (Gemini Flash)  ───▶│
    │                              │◀─── 번역된 키워드 ───────│
    │                              │  3. 프롬프트 조합         │
    │                              │  4. Imagen 4 API 호출 ──▶│
    │                              │◀─── Base64 이미지 ────────│
    │                              │  5. Base64 디코딩         │
    │                              │  6. PIL로 500×500 리사이즈│
    │                              │  7. ai_preview/ 임시 저장 │
    │◀─────────────────────────────│                         │
    │  { generation_id,            │                         │
    │    preview_url,              │                         │
    │    prompt_used }             │                         │
    │                              │                         │
    │  POST /api/ai-cover/apply    │                         │
    ├─────────────────────────────▶│                         │
    │  { path, generation_id }     │  8. 파일에 커버 임베드    │
    │                              │  9. 폴더에 cover.jpg 저장 │
    │                              │  10. 임시 파일 삭제       │
    │◀─────────────────────────────│                         │
    │  { success }                 │                         │
```

---

## 6. 백엔드 구현

### 6.1 신규 파일

```
backend/app/
├── api/
│   └── ai_cover.py              # AI 커버 생성 API 엔드포인트
└── core/
    └── ai_cover_generator.py    # Imagen 4 연동 + 프롬프트 빌더
```

### 6.2 `ai_cover_generator.py` 설계

```python
import httpx
import base64
import uuid
from pathlib import Path
from PIL import Image
import io

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# 분위기 프리셋 → 영문 키워드 매핑
MOOD_PRESETS = {
    "energetic":  "energetic, powerful, dynamic, bold, intense",
    "emotional":  "emotional, soft, romantic, dreamy, tender",
    "retro":      "retro, vintage, nostalgic, film grain, analog",
    "kpop":       "k-pop aesthetic, colorful, trendy, idol, modern",
    "jazz":       "elegant, sophisticated, minimalist, timeless",
    "hiphop":     "urban, street, bold, raw, gritty",
    "drive":      "night city, neon lights, road, cinematic, moody",
    "healing":    "serene, nature, peaceful, soft light, watercolor",
    "dark":       "dark, dramatic, powerful, cinematic, edgy",
}

YEAR_STYLES = {
    (0,    1979): "70s aesthetic, psychedelic, vinyl record era",
    (1980, 1989): "80s neon, synthwave, retro pop",
    (1990, 1999): "90s aesthetic, grunge, bright pop",
    (2000, 2009): "Y2K aesthetic, glossy, early digital",
    (2010, 2019): "modern, clean, contemporary",
    (2020, 9999): "current, trendy, minimalist digital",
}

NEGATIVE_PROMPT = (
    "text, watermark, logo, album title, artist name, letters, numbers, "
    "blurry, low quality, distorted, deformed, oversaturated"
)

class AICoverGenerator:

    def __init__(self, api_key: str, covers_path: str):
        self.api_key = api_key
        self.preview_dir = Path(covers_path) / "ai_preview"
        self.preview_dir.mkdir(parents=True, exist_ok=True)

    async def translate_hint(self, hint_ko: str) -> str:
        """한국어 힌트 → 영문 이미지 프롬프트 키워드 (Gemini Flash)"""
        url = f"{GEMINI_API_BASE}/models/gemini-2.0-flash:generateContent"
        payload = {
            "contents": [{
                "parts": [{"text": (
                    f"Translate this Korean description into English image prompt keywords "
                    f"for album cover art generation. Output only keywords, comma-separated, no explanation.\n"
                    f"Korean: {hint_ko}"
                )}]
            }]
        }
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(url, json=payload,
                                  headers={"x-goog-api-key": self.api_key})
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

    def _year_style(self, year: int | None) -> str:
        if not year:
            return ""
        for (start, end), style in YEAR_STYLES.items():
            if start <= year <= end:
                return style
        return ""

    def build_prompt(self, track_info: dict, mood: str, hint_en: str = "") -> str:
        """메타데이터 + 분위기 + 힌트 → 완성된 영문 프롬프트"""
        parts = ["Music album cover art."]

        album   = track_info.get("album_title") or track_info.get("folder_name", "")
        artist  = track_info.get("artist") or track_info.get("album_artist", "")
        genre   = track_info.get("genre", "")
        year    = track_info.get("year")

        if album:  parts.append(f'Album: "{album}".')
        if artist: parts.append(f"Artist: {artist}.")
        if genre:  parts.append(f"Genre: {genre}.")
        if year:   parts.append(f"Year: {year}.")

        mood_kw = MOOD_PRESETS.get(mood, "")
        if mood_kw: parts.append(f"Mood: {mood_kw}.")

        year_style = self._year_style(year)
        if year_style: parts.append(f"Era style: {year_style}.")

        if hint_en: parts.append(f"Additional: {hint_en}.")

        parts.append("High quality square artwork, no visible text, no watermarks.")
        return " ".join(parts)

    async def generate(
        self,
        prompt: str,
        model: str = "imagen-4.0-generate-001",
    ) -> bytes:
        """Imagen 4 API 호출 → 500×500 JPEG bytes 반환"""
        url = f"{GEMINI_API_BASE}/models/{model}:predict"
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "1:1",
                "negativePrompt": NEGATIVE_PROMPT,
            }
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, json=payload,
                                  headers={"x-goog-api-key": self.api_key})
            r.raise_for_status()
            b64 = r.json()["predictions"][0]["bytesBase64Encoded"]

        # Base64 디코딩 → PIL 리사이즈 → 500×500 JPEG
        image_bytes = base64.b64decode(b64)
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize((500, 500), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=92)
        return buf.getvalue()

    def save_preview(self, image_bytes: bytes) -> str:
        """임시 저장 → generation_id 반환"""
        gen_id = uuid.uuid4().hex
        path = self.preview_dir / f"{gen_id}.jpg"
        path.write_bytes(image_bytes)
        return gen_id

    def preview_url(self, gen_id: str) -> str:
        return f"/covers/ai_preview/{gen_id}.jpg"

    def cleanup(self, gen_id: str):
        (self.preview_dir / f"{gen_id}.jpg").unlink(missing_ok=True)
```

### 6.3 `ai_cover.py` API 엔드포인트

```
POST /api/ai-cover/generate
  Request:
    {
      "path": "/music/playlist/track01.mp3",   # 단일 파일 경로 (또는 null)
      "folder_path": "/music/playlist",         # 폴더 경로 (배치 모드)
      "mood": "energetic",                      # 분위기 프리셋 키
      "hint": "새벽 드라이브, 빗속 달리기",       # 한국어 힌트 (선택)
      "model": "imagen-4.0-generate-001",       # 모델 선택 (선택)
      "mode": "single"                          # "single" | "folder_one" | "per_file"
    }
  Response:
    {
      "generation_id": "abc123",
      "preview_url": "/covers/ai_preview/abc123.jpg",
      "prompt_used": "Music album cover art. Album: ..."
    }

POST /api/ai-cover/apply
  Request:  { "path": "...", "generation_id": "abc123" }
  Response: { "success": true }

POST /api/ai-cover/apply-folder
  Request:  { "folder_path": "...", "generation_id": "abc123" }
  Response: { "applied": 37, "failed": 0 }

DELETE /api/ai-cover/preview/{generation_id}
  Response: { "success": true }
```

### 6.4 설정 키 추가 (`config_store.py`)

```python
ai_cover_enabled          # bool — AI 커버 기능 활성화
ai_cover_gemini_api_key   # Google AI Studio API Key
ai_cover_default_mood     # 기본 분위기 프리셋 (기본: "energetic")
ai_cover_default_model    # 기본 모델 (기본: "imagen-4.0-generate-001")
```

### 6.5 임시 파일 관리

- 저장 경로: `COVERS_PATH/ai_preview/{generation_id}.jpg`
- 적용 완료 시 즉시 삭제
- TTL 1시간 자동 정리 (기존 APScheduler에 job 추가)

---

## 7. 프론트엔드 구현

### 7.1 신규 컴포넌트

```
frontend/src/components/
└── AICoverModal.vue     # AI 커버 생성 모달
```

### 7.2 `AICoverModal.vue` 화면 구성

```
┌──────────────────────────────────────────────┐
│  🎨 AI 커버아트 생성                  [✕]    │
├──────────────────────────────────────────────┤
│  대상: "운동할때 듣기 좋은노래" (37곡)        │
│  앨범: 운동할때 듣기 좋은노래                 │
│  연도: 자동 감지 (2020년대)                   │
│                                              │
│  ── 분위기 선택 ──────────────────────────   │
│  ┌────────┐ ┌────────┐ ┌────────┐           │
│  │⚡에너지틱│ │💙감성  │ │📻레트로│  ...      │
│  └────────┘ └────────┘ └────────┘           │
│                                              │
│  ── 추가 키워드 (선택) ──────────────────    │
│  ┌──────────────────────────────────────┐   │
│  │ 예: 새벽 드라이브, 빗속 달리기...     │   │
│  └──────────────────────────────────────┘   │
│  (한국어 입력 가능 — 자동 번역됨)            │
│                                              │
│  ── 적용 모드 ───────────────────────────   │
│  ● 전체에 동일 이미지 적용 (1회 생성·저렴)  │
│  ○ 파일마다 개별 생성                        │
│                                              │
│  모델: [표준 ▼]   [🎨 생성하기]             │
├──────────────────────────────────────────────┤
│  [미리보기]                                  │
│  ┌──────────┐  500×500 · JPEG               │
│  │          │  "Music album cover art.       │
│  │  이미지  │   Album: 운동할때..."           │
│  │          │                                │
│  └──────────┘  [🔄 다시 생성] [✅ 적용]      │
└──────────────────────────────────────────────┘
```

### 7.3 진입점

| 위치 | 조건 | 버튼 |
|------|------|------|
| `TagPanel.vue` | `!file.has_cover` | "🎨 AI 커버 생성" (커버 없을 때만) |
| `Browser.vue` 툴바 | 폴더에 커버 없는 파일 1개 이상 | "🎨 AI 커버" 버튼 |
| `AlbumDetail.vue` | `!album.cover_path` | "🎨 AI 생성" 버튼 |

### 7.4 API 클라이언트

```javascript
// frontend/src/api/index.js
aiCoverApi: {
  generate:     (data) => client.post('/ai-cover/generate', data),
  apply:        (data) => client.post('/ai-cover/apply', data),
  applyFolder:  (data) => client.post('/ai-cover/apply-folder', data),
  deletePreview:(id)   => client.delete(`/ai-cover/preview/${id}`),
}
```

### 7.5 Settings 페이지 추가 항목

```
[🎨 AI 커버아트 생성]
  ┌────────────────────────────────────────┐
  │ Google AI Studio API 키                │
  │ [●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●] │
  │                                        │
  │ 기본 분위기: [에너지틱 ▼]              │
  │ 기본 모델:   [표준 (imagen-4.0) ▼]    │
  │                                        │
  │ API 키 발급: ai.google.dev             │
  └────────────────────────────────────────┘
```

---

## 8. 구현 단계

### Phase 1 — 백엔드 (1~2일)
- [ ] `ai_cover_generator.py`: Imagen 4 연동, 프롬프트 빌더, 한국어 힌트 번역
- [ ] `ai_cover.py`: generate / apply / apply-folder 엔드포인트
- [ ] `config_store.py`: `ai_cover_*` 설정 키 4개 추가
- [ ] `main.py`: `ai_cover` 라우터 등록
- [ ] APScheduler: 미리보기 TTL 정리 job 추가

### Phase 2 — 프론트엔드 (1~2일)
- [ ] `AICoverModal.vue`: 분위기 선택 + 키워드 입력 + 미리보기 UI
- [ ] `Settings.vue`: AI 커버 설정 섹션 추가
- [ ] `TagPanel.vue`: `!file.has_cover` 조건부 "AI 커버 생성" 버튼
- [ ] `Browser.vue`: 툴바 AI 커버 버튼
- [ ] `api/index.js`: `aiCoverApi` 추가
- [ ] i18n ko/en: `aiCover.*` 키 추가

### Phase 3 — 배치 모드 (1일)
- [ ] 폴더 단일 이미지 모드 (`apply-folder`)
- [ ] 배치 개별 생성 시 진행률 표시 (SSE 또는 폴링)

---

## 9. 비용 추정

| 시나리오 | 모델 | 생성 횟수 | 예상 비용 |
|---------|------|-----------|-----------|
| 단일 파일 | 표준 | 1회 | ~$0.03 |
| 30곡 (폴더 단일 이미지) | 표준 | 1회 | ~$0.03 |
| 30곡 (파일별 개별) | fast | 30회 | ~$0.30 |
| 100곡 (파일별 개별) | fast | 100회 | ~$1.00 |
| 한국어 힌트 번역 (추가) | Gemini Flash | — | ~$0.00 |

→ **기본 모드를 "폴더 단일 이미지"로 설정**하여 비용 최소화

---

## 10. 제약 사항 및 고려사항

### API 제약
- Imagen 4: 영어 프롬프트만 지원 → 한국어 힌트는 Gemini Flash로 자동 번역
- Rate limit: AI Studio 무료 티어 10 RPM, 유료 티어 2,000 RPM
- 배치 생성 시 1~2초 간격 요청 (rate limit 회피)

### 이미지 처리
- 생성 크기: 1K (약 1024px 정방형)
- 최종 저장 크기: **500×500 JPEG** (PIL LANCZOS 리사이즈, quality=92)
- 기존 `tag_writer.write_cover()`는 최대 1200px 리사이즈 로직 포함 → 500px 이미지는 그대로 통과

### 저작권
- Imagen 4 생성 이미지: 사용자에게 저작권 귀속 (Google AI Studio ToS)
- SynthID 비가시적 워터마크 포함 (AI 생성물 식별용, 육안 불가)

---

## 11. 관련 파일 변경 요약

| 파일 | 변경 유형 | 내용 |
|------|-----------|------|
| `backend/app/api/ai_cover.py` | **신규** | Imagen 4 연동 API (generate/apply/apply-folder) |
| `backend/app/core/ai_cover_generator.py` | **신규** | 프롬프트 빌더, 번역, 이미지 생성·리사이즈 |
| `backend/app/core/config_store.py` | 수정 | `ai_cover_*` 설정 키 4개 추가 |
| `backend/app/main.py` | 수정 | `ai_cover` 라우터 등록 |
| `frontend/src/components/AICoverModal.vue` | **신규** | 분위기 선택, 키워드 입력, 미리보기 UI |
| `frontend/src/components/TagPanel.vue` | 수정 | 커버 없을 때 AI 생성 버튼 |
| `frontend/src/views/Browser.vue` | 수정 | 툴바 AI 커버 버튼 |
| `frontend/src/views/Settings.vue` | 수정 | AI 커버 설정 섹션 |
| `frontend/src/api/index.js` | 수정 | `aiCoverApi` 추가 |
| `frontend/src/i18n/ko.js` | 수정 | `aiCover.*` 키 추가 |
| `frontend/src/i18n/en.js` | 수정 | `aiCover.*` 키 추가 |
