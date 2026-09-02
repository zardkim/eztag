<template>
  <div>
    <!-- 디자인 스펙: padding 3px 6px / gap 4px / radius 4px / font-size 12px,
         들여쓰기 6 + depth*14, 선택 시 accent-weak 배경 + accent-ink 글자 (약한 강조) -->
    <div
      class="w-full flex items-center gap-1 pr-1.5 rounded transition-colors group"
      :class="[
        mobile ? 'py-2 text-[13px]' : 'py-[3px] text-xs',
        isSelected
          ? 'bg-indigo-50 text-indigo-700 font-medium dark:bg-indigo-950/50 dark:text-indigo-300'
          : 'text-gray-800 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
      ]"
      :style="{ paddingLeft: `${6 + depth * indentStep}px` }"
    >
      <!-- 펼치기/접기 캐럿 (클릭 시 트리만 토글) -->
      <span
        class="shrink-0 flex items-center justify-center cursor-pointer transition-transform text-gray-400 dark:text-gray-600"
        :class="[mobile ? 'w-7 h-7 -my-1' : 'w-3.5 h-3.5', open ? 'rotate-90' : '']"
        @click="toggleExpand"
      >
        <svg v-if="node.has_children || node.isRoot" class="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none">
          <path d="M6 3l5 5-5 5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </span>

      <!-- 폴더 이름 (클릭 시 폴더 선택) -->
      <button
        class="flex-1 flex items-center gap-1 text-left min-w-0"
        @click="selectNode"
      >
        <!-- 폴더 아이콘 색상으로 영역을 구분한다 (작업공간=주황 / 라이브러리=파랑).
             선택 여부와 무관하게 유지해야 구분이 깨지지 않는다. -->
        <span
          class="shrink-0 w-3.5 h-3.5 flex items-center justify-center"
          :class="areaIconClass"
        >
          <svg v-if="open" class="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none">
            <path d="M1.5 4.5v7a1 1 0 0 0 1 1h11a1 1 0 0 0 .96-.72l1.1-4A1 1 0 0 0 14.6 6H4.1a1 1 0 0 0-.96.72L1.5 12" stroke="currentColor" stroke-width="1.2" />
            <path d="M1.5 4.5v-1a1 1 0 0 1 1-1h4L8 4.5h4.5a1 1 0 0 1 1 1v1" stroke="currentColor" stroke-width="1.2" />
          </svg>
          <svg v-else class="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none">
            <path d="M1.5 4.5v7a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1V5.5a1 1 0 0 0-1-1H8L6.5 3h-4a1 1 0 0 0-1 1Z" stroke="currentColor" stroke-width="1.2" />
          </svg>
        </span>
        <span :class="mobile ? 'line-clamp-2 break-all' : 'truncate'" :title="node.name">{{ node.name }}</span>
        <!-- 디자인의 count 뱃지 자리 — 트랙 수 데이터가 없어 오디오 유무만 표시 (계획서 §7 ①) -->
        <span
          v-if="node.has_audio"
          class="ml-auto shrink-0 font-mono text-[10px] leading-none"
          :class="isSelected ? 'text-indigo-400 dark:text-indigo-500' : 'text-gray-400 dark:text-gray-600'"
        >♪</span>
      </button>
    </div>

    <!-- Children -->
    <div v-if="open && children.length > 0">
      <FolderNode
        v-for="child in children"
        :key="child.path"
        :node="child"
        :depth="depth + 1"
        :area="area"
        :mobile="mobile"
        :ancestors="childAncestors"
        :selected-path="selectedPath"
        @select="$emit('select', $event)"
      />
    </div>
    <div v-if="open && loadingChildren" class="py-0.5" :style="{ paddingLeft: `${26 + depth * indentStep}px` }">
      <span class="text-[11px] text-gray-400 dark:text-gray-600">…</span>
    </div>
    <div v-if="open && loadError" class="py-0.5" :style="{ paddingLeft: `${26 + depth * indentStep}px` }">
      <span class="text-[11px] text-red-400">{{ $t('browser.folderOpenFailed') }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { browseApi } from '../api/index.js'
import { sessionCache } from '../utils/cache.js'

const props = defineProps({
  node: Object,
  depth: { type: Number, default: 0 },
  // 이 노드가 속한 영역 ('workspace' | 'library') — 루트에서 자식까지 그대로 전파
  area: { type: String, default: null },
  // 루트부터 이 노드의 부모까지의 체인 [{ name, path }, ...]
  ancestors: { type: Array, default: () => [] },
  selectedPath: { type: String, default: null },
  // 모바일 바텀시트용 — 들여쓰기 축소 + 터치 타깃 확대 + 이름 2줄
  mobile: { type: Boolean, default: false },
  initialChildren: { type: Array, default: null },
})
const emit = defineEmits(['select'])

const CHILDREN_TTL_MS = 5 * 60 * 1000  // 5분
const cacheKey = `children:${props.node.path}`

const open = ref(false)
const loadingChildren = ref(false)
const loadError = ref(false)

// initialChildren 또는 sessionStorage 캐시에서 초기값 설정
const _cached = props.initialChildren ?? sessionCache.get(cacheKey)
const children = ref(_cached ?? [])
const loadedAt = ref(_cached ? Date.now() : 0)

const isSelected = computed(() => props.selectedPath === props.node.path)
const indentStep = computed(() => (props.mobile ? 10 : 14))

// 영역별 폴더 아이콘 색상 — 작업공간(주황) / 라이브러리(파랑)
const areaIconClass = computed(() => {
  if (props.area === 'workspace') return 'text-orange-500 dark:text-orange-400'
  if (props.area === 'library')   return 'text-blue-500 dark:text-blue-400'
  return 'text-gray-500 dark:text-gray-400'
})

// 자기 자신을 포함한 조상 체인 — 자식에게 내려보내고 breadcrumb 생성에 사용
const self = computed(() => ({ name: props.node.name, path: props.node.path }))
const childAncestors = computed(() => [...props.ancestors, self.value])

async function loadChildren(force = false) {
  // 메모리에 있고 TTL 이내면 스킵
  const stale = Date.now() - loadedAt.value > CHILDREN_TTL_MS
  if (!force && children.value.length > 0 && !stale) return

  // sessionStorage 캐시 확인
  if (!force) {
    const cached = sessionCache.get(cacheKey)
    if (cached) {
      children.value = cached
      loadedAt.value = Date.now()
      return
    }
  }

  loadingChildren.value = true
  loadError.value = false
  try {
    const { data } = await browseApi.getChildren(props.node.path, force)
    children.value = data
    loadedAt.value = Date.now()
    sessionCache.set(cacheKey, data, CHILDREN_TTL_MS)
  } catch {
    loadError.value = true
    children.value = []
  } finally {
    loadingChildren.value = false
  }
}

function toggleExpand() {
  if (!props.node.has_children && !props.node.isRoot) return
  open.value = !open.value
  if (open.value) loadChildren()
}

function selectNode() {
  // area와 조상 체인을 함께 올려보낸다.
  // /browse/children 응답에는 area가 없으므로 트리 루트에서 받은 값을 그대로 전파한다.
  emit('select', {
    node: props.node,
    area: props.area,
    crumb: childAncestors.value,
  })
  // 자식이 있으면 선택 시 자동으로 펼침 + 강제 새로고침 (외부 변경 감지)
  if (props.node.has_children || props.node.isRoot) {
    open.value = true
    loadChildren(true)
  }
}
</script>
