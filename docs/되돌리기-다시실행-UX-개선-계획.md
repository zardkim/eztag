# 되돌리기/다시 실행 UX 개선 계획서

## 현황 분석

### 현재 구조

```
Browser.vue (상단 앱 툴바)
  └─ Teleport → #app-toolbar-slot
       ├─ [↩ 되돌리기]  ← historyStore.undo()
       ├─ [다시 실행 ↪] ← historyStore.redo()
       └─ [🔄 새로고침]
```

| 항목 | 현재 위치 | 문제 |
|------|-----------|------|
| 되돌리기/다시 실행 버튼 | 파일 목록 상단 툴바 | 파일 목록에서는 무관한 기능 |
| historyStore.push() 호출 | `TagPanel.vue`, `BatchTagPanel.vue` | 태그 편집만 등록됨 |
| 자동태그 되돌리기 | `AutoTagDialog.vue` 내부 버튼 | 별도 API(`revertAutoTag`) 사용, historyStore 미연동 |
| 자동태그 redo | 없음 | 지원 안 됨 |

---

### historyStore 동작 방식 (현재)

- **push(entry)**: `{ label, ops: [{path, before, after}] }` 엔트리를 스택에 저장
- **undo(browserStore)**: `op.before` 상태를 `browseApi.batchWriteTags`로 파일에 직접 기록
- **redo(browserStore)**: `op.after` 상태를 동일하게 파일에 기록
- **자동태그의 되돌리기**: historyStore와 무관하게 `metaApi.revertAutoTag(paths)` API 호출 (백엔드가 백업 태그 복원)

---

## 문제점 정리

### 1. 위치 부적절
되돌리기/다시 실행은 파일 목록을 보는 행위가 아니라 **태그를 편집한 직후** 필요한 기능.
상단 툴바 상시 노출은 컨텍스트에 맞지 않음.

### 2. 자동태그 앨범 모드 되돌리기 없음
- AutoTagDialog 앨범 모드(`applyAlbum`)는 적용 후 되돌리기 수단이 전혀 없음
- historyStore에 등록하면 TagPanel/BatchTagPanel과 동일한 undo/redo 가능

### 3. 적용 위치 불일치
- TagPanel, BatchTagPanel → historyStore.push() ✓
- AutoTagDialog 파일명 모드 → 전용 revertAutoTag 버튼 존재 (유지)
- AutoTagDialog 앨범 모드 → historyStore 미사용 → 연동 필요

---

## 목표 구조

```
상단 툴바: 되돌리기/다시 실행 버튼 제거

TagPanel (우측 태그 편집 패널)
  └─ 저장/취소 버튼 아래에 [↩ 되돌리기] [다시 실행 ↪] 상시 표시
     (historyStore.canUndo/canRedo 로 활성화 제어)

BatchTagPanel (일괄 태그 편집 패널)
  └─ 동일 패턴

AutoTagDialog (자동태그 다이얼로그)
  └─ 파일명 모드: 기존 revertAutoTag 버튼 유지
  └─ 앨범 모드: 적용 전 스냅샷 → historyStore.push() → 되돌리기/다시실행 가능
```

---

## 상세 변경 계획

### 변경 1 — Browser.vue: 상단 툴바에서 되돌리기/다시 실행 제거

**파일**: `frontend/src/views/Browser.vue`

- 데스크톱 툴바 `↩ 되돌리기`, `다시 실행 ↪` 버튼 2개 제거
- 모바일 툴바 동일 버튼 2개 제거
- `import { useHistoryStore }` 및 `const historyStore` 선언 제거

---

### 변경 2 — TagPanel.vue: 저장 버튼 하단에 인라인 undo/redo 추가

**파일**: `frontend/src/components/TagPanel.vue`

저장/취소 버튼 행 아래에 되돌리기/다시 실행 행 추가:

```
┌─────────────────────────────────────────┐
│ [저장]          [취소]                   │
│ [↩ 되돌리기]   [다시 실행 ↪]            │ ← 신규
└─────────────────────────────────────────┘
```

- `historyStore.canUndo` / `canRedo` 로 버튼 활성화
- `historyStore.undo(browserStore)` / `redo(browserStore)` 호출

---

### 변경 3 — BatchTagPanel.vue: 동일 패턴 적용

**파일**: `frontend/src/components/BatchTagPanel.vue`

- TagPanel과 동일하게 저장/초기화 버튼 행 아래에 undo/redo 행 추가

---

### 변경 4 — AutoTagDialog.vue: 앨범 모드 historyStore 연동

**파일**: `frontend/src/components/AutoTagDialog.vue`

- `applyAlbum()` 시작 전: `localFiles.value` 각 파일의 현재 태그 스냅샷 수집
- 적용 완료 후: `historyStore.push({ label, ops })` 등록
- 파일명 모드의 `revertAutoTag` 버튼은 그대로 유지 (변경 없음)

---

## 파일별 변경 요약

| 파일 | 변경 내용 | 난이도 |
|------|-----------|--------|
| `Browser.vue` | 툴바 버튼 2개 × 2(데스크톱/모바일) 제거, historyStore 의존 제거 | 낮음 |
| `TagPanel.vue` | 저장 버튼 하단 undo/redo 행 추가 | 낮음 |
| `BatchTagPanel.vue` | 동일 패턴 | 낮음 |
| `AutoTagDialog.vue` | 앨범 모드 applyAlbum() 스냅샷 + historyStore.push() | 중간 |

---

## 구현 순서

1. `Browser.vue` — 툴바 되돌리기/다시 실행 버튼 제거
2. `TagPanel.vue` — 저장 완료 후 인라인 버튼 추가
3. `BatchTagPanel.vue` — 동일 패턴 적용
4. `AutoTagDialog.vue` — 앨범 모드 historyStore 연동
