<template>
  <div>
    <div
      class="w-full flex items-center rounded-md text-sm transition-colors group"
      :class="isSelected
        ? 'bg-blue-600 text-white'
        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'"
      :style="{ paddingLeft: `${8 + depth * 14}px` }"
    >
      <!-- 펼치기/접기 화살표 (클릭 시 트리만 토글) -->
      <span
        class="shrink-0 w-6 h-7 flex items-center justify-center cursor-pointer transition-transform"
        :class="open ? 'rotate-90' : ''"
        @click="toggleExpand"
      >
        <svg v-if="node.has_children || node.isRoot" class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
        </svg>
        <span v-else class="w-3 h-3 inline-block" />
      </span>

      <!-- 폴더 이름 (클릭 시 폴더 선택) -->
      <button
        class="flex-1 flex items-center gap-1.5 py-1.5 pr-2 text-left min-w-0"
        @click="selectNode"
      >
        <span class="shrink-0 text-xs">{{ open ? '📂' : '📁' }}</span>
        <span class="truncate text-xs">{{ node.name }}</span>
        <span v-if="node.has_audio && !isSelected" class="shrink-0 text-xs text-gray-400 dark:text-gray-600">🎵</span>
      </button>
    </div>

    <!-- Children -->
    <div v-if="open && children.length > 0">
      <FolderNode
        v-for="child in children"
        :key="child.path"
        :node="child"
        :depth="depth + 1"
        :selected-path="selectedPath"
        @select="$emit('select', $event)"
      />
    </div>
    <div v-if="open && loadingChildren" class="pl-8 py-1">
      <span class="text-xs text-gray-400">...</span>
    </div>
    <div v-if="open && loadError" class="pl-8 py-1">
      <span class="text-xs text-red-400">폴더를 열 수 없습니다</span>
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
  selectedPath: { type: String, default: null },
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
  emit('select', props.node)
  // 자식이 있으면 선택 시 자동으로 펼침 + 강제 새로고침 (외부 변경 감지)
  if (props.node.has_children || props.node.isRoot) {
    open.value = true
    loadChildren(true)
  }
}
</script>
