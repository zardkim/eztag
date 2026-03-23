# AI 커버아트 생성 기능 구현 계획서

> **버전**: 1.0
> **작성일**: 2026-03-23
> **대상 버전**: eztag v0.7.0

---

## 1. 배경 및 목적

멜론/벅스 차트 모음, 운동 플레이리스트 등 인터넷에서 수집한 음악 파일은 앨범아트가 없는 경우가 많다. 기존에는 Google CSE, Spotify 등 외부 이미지를 가져오는 방식을 사용했지만, 검색 결과가 없거나 플레이리스트 성격의 컬렉션에는 적합하지 않다.

**AI 이미지 생성 모델(DALL-E / Stable Diffusion 등)과 연동**하여 트랙 메타데이터(아티스트, 제목, 장르 등)를 기반으로 어울리는 커버아트를 자동 생성하는 기능을 추가한다.

---

## 2. 사용 시나리오

### 시나리오 A — 단일 파일 커버 생성
1. 파일 브라우저에서 커버가 없는 파일 선택
2. TagPanel 또는 브라우저 툴바에서 "AI 커버 생성" 버튼 클릭
3. 트랙 정보(제목, 아티스트, 장르)가 자동으로 프롬프트에 반영됨
4. 프롬프트 미리보기/수정 후 생성 요청
5. 결과 이미지 미리보기 → 마음에 들면 파일에 즉시 임베드

### 시나리오 B — 폴더 일괄 생성
1. 커버가 없는 파일이 있는 폴더를 열었을 때 브라우저 툴바에 배지 표시
2. "AI 커버 일괄 생성" 클릭
3. 커버 없는 파일 목록 확인 (체크박스 선택)
4. 공통 스타일(분위기, 색상 톤) 선택 후 일괄 생성
5. 생성된 이미지 썸네일 리뷰 → 전체 적용 or 개별 선택 적용

### 시나리오 C — 플레이리스트 대표 이미지
1. 폴더 전체에 단일 커버 이미지를 적용하고 싶을 때
2. 폴더명/분위기를 기반으로 하나의 이미지 생성
3. 폴더 내 전체 파일에 동일 이미지 일괄 임베드

---

## 3. 지원 AI 모델

| 제공자 | 모델 | API 방식 | 비용 | 비고 |
|--------|------|----------|------|------|
| **OpenAI** | DALL-E 3 | REST API (유료) | ~$0.04/장 (1024×1024) | 품질 최상, 한국어 프롬프트 지원 |
| **OpenAI** | DALL-E 2 | REST API (유료) | ~$0.018/장 | DALL-E 3보다 저렴 |
| **Stability AI** | Stable Diffusion 3 | REST API (유료) | ~$0.03/장 | 스타일 제어 우수 |
| **로컬** | Stable Diffusion (AUTOMATIC1111/ComfyUI) | REST API (무료) | GPU 필요 | 자체 서버 운영 시 |

**v0.7.0 구현 범위**: OpenAI DALL-E 3 우선 지원, 이후 Stable Diffusion API 추가

---

## 4. 아키텍처 설계

### 4.1 전체 흐름

```
[프론트엔드]                [백엔드]                    [AI API]
    │                          │                           │
    │  POST /api/ai-cover/      │                           │
    │  generate                 │                           │
    ├──────────────────────────▶│                           │
    │  { path, prompt_hint,     │  1. 트랙 메타데이터 조회  │
    │    style, provider }      │  2. 프롬프트 조합         │
    │                          │  3. API 호출 ────────────▶│
    │                          │                           │
    │                          │◀──── image URL / bytes ───│
    │                          │  4. 이미지 다운로드        │
    │                          │  5. covers/ 에 임시 저장  │
    │◀──────────────────────────│                           │
    │  { preview_url,           │                           │
    │    generation_id }        │                           │
    │                          │                           │
    │  POST /api/ai-cover/      │                           │
    │  apply                    │                           │
    ├──────────────────────────▶│                           │
    │  { path, generation_id }  │  6. 파일에 커버 임베드    │
    │                          │  7. cover.jpg 저장        │
    │◀──────────────────────────│                           │
    │  { success }              │                           │
```

### 4.2 프롬프트 설계

트랙 메타데이터를 기반으로 AI 프롬프트를 자동 구성한다.

#### 기본 프롬프트 템플릿
```
Album cover art for "{title}" by {artist}.
Genre: {genre}. Style: {style_preset}.
High quality, square format, music album artwork.
No text, no watermarks.
```

#### 스타일 프리셋 (사용자 선택)

| 프리셋 | 프롬프트 키워드 | 적합한 장르 |
|--------|----------------|------------|
| **Minimal** | minimalist, clean lines, geometric, modern | 팝, 일렉트로닉 |
| **Vivid** | vibrant colors, energetic, dynamic, bold | 운동, 힙합, 팝 |
| **Calm** | soft colors, peaceful, serene, watercolor | 발라드, 재즈, 클래식 |
| **Retro** | vintage, retro aesthetic, film grain, 70s/80s | 레트로, 록 |
| **Abstract** | abstract art, surreal, artistic, impressionist | 아트팝, 인디 |
| **Dark** | dark atmosphere, moody, dramatic, cinematic | 록, 메탈, R&B |
| **K-pop** | k-pop aesthetic, colorful, idol, trendy | K-pop, 댄스 |

#### 특수 케이스 처리
- **차트 모음** (제목에 "차트", "TOP", "Best" 포함): 다채로운 콜라주 스타일
- **운동 플레이리스트** (제목에 "운동", "workout", "gym" 포함): 에너지틱, 모션 블러
- **드라이브 모음**: 야경, 도로, 속도감
- **감성 모음**: 따뜻한 색감, 자연, 보케 효과

### 4.3 배치 생성 전략

여러 파일에 동시에 적용할 때:
- 옵션 A: **파일마다 개별 생성** — 각 트랙에 맞는 이미지, API 비용 증가
- 옵션 B: **폴더 단일 이미지** — 1회 생성 후 전체 파일에 동일 적용, 경제적
- 옵션 C: **앨범 단위 공유** — 같은 앨범 아티스트의 파일은 1개 이미지 공유

→ 사용자가 모드를 선택할 수 있도록 UI 제공

---

## 5. 백엔드 구현

### 5.1 신규 파일

```
backend/app/
├── api/
│   └── ai_cover.py              # AI 커버 생성 API 엔드포인트
└── core/
    └── ai_cover_generator.py    # AI API 연동 + 프롬프트 생성 로직
```

### 5.2 `ai_cover_generator.py` 설계

```python
class AICoverGenerator:
    """AI 이미지 생성 API 연동"""

    def build_prompt(self, track_info: dict, style: str, hint: str = "") -> str:
        """트랙 메타데이터 → 영문 프롬프트 변환"""

    async def generate_dalle(self, prompt: str, api_key: str, size: str = "1024x1024") -> bytes:
        """OpenAI DALL-E 3 API 호출 → 이미지 bytes 반환"""

    async def generate_stability(self, prompt: str, api_key: str) -> bytes:
        """Stability AI API 호출 → 이미지 bytes 반환"""

    def save_preview(self, image_bytes: bytes, generation_id: str) -> str:
        """임시 폴더에 미리보기 이미지 저장 → 상대 경로 반환"""

    def cleanup_preview(self, generation_id: str):
        """미리보기 임시 파일 삭제"""
```

### 5.3 `ai_cover.py` API 엔드포인트

```
POST /api/ai-cover/generate
  Request:  { path, style, prompt_hint, provider }
  Response: { generation_id, preview_url, prompt_used }

POST /api/ai-cover/generate-batch
  Request:  { paths, style, prompt_hint, provider, mode }
  Response: { generation_id, previews: [{ path, preview_url }] }

POST /api/ai-cover/apply
  Request:  { path, generation_id }
  Response: { success }

POST /api/ai-cover/apply-batch
  Request:  { items: [{ path, generation_id }] }
  Response: { applied, failed }

DELETE /api/ai-cover/preview/{generation_id}
  Response: { success }
```

### 5.4 설정 키 추가 (`config_store.py`)

```python
ai_cover_provider       # "openai" | "stability" | "local"
ai_cover_openai_key     # OpenAI API Key
ai_cover_stability_key  # Stability AI API Key
ai_cover_local_url      # 로컬 SD API URL (예: http://192.168.1.x:7860)
ai_cover_default_style  # 기본 스타일 프리셋
ai_cover_enabled        # bool
```

### 5.5 임시 파일 관리

- 생성된 미리보기 이미지: `COVERS_PATH/ai_preview/{generation_id}.jpg`
- TTL: 1시간 (사용하지 않으면 자동 삭제, APScheduler job 추가)
- 적용 완료 시 즉시 삭제

---

## 6. 프론트엔드 구현

### 6.1 신규 컴포넌트

```
frontend/src/components/
└── AICoverModal.vue     # AI 커버 생성 모달 (단일 + 배치)
```

### 6.2 `AICoverModal.vue` 화면 구성

```
┌─────────────────────────────────────────┐
│  🎨 AI 커버아트 생성          [✕]        │
├─────────────────────────────────────────┤
│  대상: "운동할때 듣기 좋은노래 (37곡)"   │
│                                          │
│  [스타일 선택]                           │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │
│  │Vivid │ │Calm  │ │Retro │ │Dark  │  │
│  └──────┘ └──────┘ └──────┘ └──────┘  │
│                                          │
│  [프롬프트 힌트 (선택)]                  │
│  ┌────────────────────────────────────┐ │
│  │ 예: 새벽 드라이브, 빗속 달리기...  │ │
│  └────────────────────────────────────┘ │
│                                          │
│  적용 모드:                              │
│  ● 전체에 동일 이미지 적용 (1회 생성)   │
│  ○ 파일마다 개별 생성                   │
│                                          │
│         [생성하기]                       │
├─────────────────────────────────────────┤
│  [미리보기 영역]                         │
│  ┌──────────┐                           │
│  │          │  "에너지틱하고 역동적인..."│
│  │  이미지  │                           │
│  │          │  [다시 생성] [파일에 적용] │
│  └──────────┘                           │
└─────────────────────────────────────────┘
```

### 6.3 진입점 (UI 연결)

| 위치 | 조건 | 버튼 |
|------|------|------|
| `TagPanel.vue` | `!file.has_cover` | "🎨 AI 커버 생성" 버튼 (커버 없을 때만 표시) |
| `Browser.vue` 툴바 | 폴더에 커버 없는 파일 존재 | "🎨 AI 일괄 생성" 버튼 |
| `AlbumDetail.vue` | 앨범 커버 없음 | "🎨 AI 생성" 버튼 |

### 6.4 API 클라이언트 추가

```javascript
// frontend/src/api/index.js
aiCoverApi: {
  generate: (data) => client.post('/ai-cover/generate', data),
  generateBatch: (data) => client.post('/ai-cover/generate-batch', data),
  apply: (data) => client.post('/ai-cover/apply', data),
  applyBatch: (data) => client.post('/ai-cover/apply-batch', data),
  deletePreview: (id) => client.delete(`/ai-cover/preview/${id}`),
}
```

### 6.5 Settings 페이지 추가

```
[AI 커버아트 생성]
  ┌─────────────────────────────────────┐
  │ 제공자: [OpenAI DALL-E ▼]          │
  │ API 키: [●●●●●●●●●●●●●●●●●●●●●]  │
  │ 기본 스타일: [Vivid ▼]             │
  └─────────────────────────────────────┘
```

---

## 7. 구현 단계

### Phase 1 — 백엔드 기반 (1~2일)
- [ ] `ai_cover_generator.py`: OpenAI DALL-E 3 연동
- [ ] `ai_cover.py`: generate / apply 엔드포인트
- [ ] `config_store.py`: AI 커버 설정 키 추가
- [ ] 임시 파일 TTL 정리 (APScheduler job)

### Phase 2 — 프론트엔드 기반 (1~2일)
- [ ] `AICoverModal.vue`: 스타일 선택 + 프롬프트 힌트 + 미리보기 UI
- [ ] `Settings.vue`: AI 커버 설정 섹션 추가
- [ ] `TagPanel.vue`: 커버 없을 때 "AI 생성" 버튼 추가
- [ ] `api/index.js`: aiCoverApi 추가
- [ ] i18n (ko/en) 키 추가

### Phase 3 — 배치 기능 (1일)
- [ ] `generate-batch` / `apply-batch` 엔드포인트
- [ ] `Browser.vue` 툴바: "AI 일괄 생성" 버튼 + 배치 모달 확장

### Phase 4 — 추가 제공자 지원 (선택, 이후 버전)
- [ ] Stability AI API 연동
- [ ] 로컬 AUTOMATIC1111 / ComfyUI API 연동
- [ ] 프롬프트 히스토리 저장

---

## 8. 비용 추정 (OpenAI DALL-E 3 기준)

| 사용 시나리오 | 생성 횟수 | 예상 비용 |
|--------------|-----------|-----------|
| 단일 파일 생성 | 1회 | ~$0.04 |
| 30곡 플레이리스트 (동일 이미지) | 1회 | ~$0.04 |
| 30곡 플레이리스트 (개별 생성) | 30회 | ~$1.20 |
| 100곡 라이브러리 정리 (개별) | 100회 | ~$4.00 |

→ "전체에 동일 이미지 적용" 모드 기본값으로 설정해 비용 절감 유도

---

## 9. 제약 사항 및 고려 사항

### API 제약
- OpenAI DALL-E 3: 분당 생성 제한 (Tier 1: 5 RPM, Tier 2: 50 RPM)
- 배치 생성 시 rate limit 처리 필요 (지수 백오프 재시도)
- 응답 이미지는 URL 형태로 반환 (1시간 후 만료) → 즉시 다운로드 필요

### 이미지 품질
- DALL-E 3 출력: 1024×1024 → `tag_writer.write_cover()`의 리사이즈(1200px) 로직 통과
- 생성된 이미지에 텍스트가 포함될 수 있음 → 프롬프트에 "No text" 명시

### 저작권
- AI 생성 이미지의 저작권은 사용자에게 귀속 (OpenAI ToS 기준)
- 개인 라이브러리 관리 목적으로 사용 시 문제 없음

### 로컬 SD 지원 시
- AUTOMATIC1111 기본 포트: `7860`
- ComfyUI 기본 포트: `8188`
- 텍스트-이미지 엔드포인트: `POST /sdapi/v1/txt2img`

---

## 10. 관련 파일 변경 요약

| 파일 | 변경 유형 | 내용 |
|------|-----------|------|
| `backend/app/api/ai_cover.py` | 신규 | AI 커버 생성/적용 API |
| `backend/app/core/ai_cover_generator.py` | 신규 | AI API 연동 + 프롬프트 빌더 |
| `backend/app/core/config_store.py` | 수정 | AI 커버 설정 키 추가 |
| `backend/app/main.py` | 수정 | `ai_cover` 라우터 등록 |
| `frontend/src/components/AICoverModal.vue` | 신규 | 생성 UI 모달 |
| `frontend/src/components/TagPanel.vue` | 수정 | AI 생성 버튼 추가 |
| `frontend/src/views/Browser.vue` | 수정 | 툴바 AI 일괄 생성 버튼 |
| `frontend/src/views/Settings.vue` | 수정 | AI 커버 설정 섹션 |
| `frontend/src/api/index.js` | 수정 | `aiCoverApi` 추가 |
| `frontend/src/i18n/ko.js` | 수정 | aiCover.* 키 추가 |
| `frontend/src/i18n/en.js` | 수정 | aiCover.* 키 추가 |
