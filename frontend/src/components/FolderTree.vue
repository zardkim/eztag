<template>
  <div class="flex flex-col h-full min-h-0">
    <!-- pane 헤더: 디자인 스펙 padding 8px 12px / min-height 40px,
         제목 12px·600·uppercase·letter-spacing .04em -->
    <div v-if="!hideHeader" class="px-3 py-2 min-h-[40px] flex items-center gap-0.5 shrink-0 border-b border-gray-200 dark:border-gray-800">
      <span class="flex-1 min-w-0 text-xs font-semibold text-gray-500 dark:text-gray-500 uppercase tracking-[0.04em]">{{ $t('browser.folders') }}</span>
      <RouterLink
        to="/home"
        class="w-6 h-6 flex items-center justify-center rounded text-gray-400 hover:text-gray-700 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        active-class="text-gray-900 bg-gray-100 dark:text-white dark:bg-gray-800"
        :title="$t('nav.home')"
      >
        <svg class="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none">
          <path d="M2 6.5 8 2l6 4.5V13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V6.5Z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round" />
          <path d="M6.25 14V9.5h3.5V14" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round" />
        </svg>
      </RouterLink>
      <button
        class="w-6 h-6 flex items-center justify-center rounded text-gray-400 hover:text-gray-700 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        :class="loading ? 'animate-spin' : ''"
        :title="$t('browser.refreshFolders')"
        :disabled="loading"
        @click="refreshRoots"
      >
        <svg class="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none">
          <path d="M13.5 8a5.5 5.5 0 1 1-1.8-4.1" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
          <path d="M13.5 2v3h-3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
    </div>

    <div v-if="loading" class="px-3 py-2 text-xs text-gray-400">{{ $t('common.loading') }}</div>
    <div v-else-if="visibleSections.length === 0" class="px-3 py-2 text-xs text-gray-400">{{ $t('browser.noFolders') }}</div>

    <!-- 트리 컨테이너: 디자인 .tree { padding: 4px } -->
    <div v-else class="flex-1 overflow-y-auto min-h-0 p-1">
      <template v-for="section in visibleSections" :key="section.key">
        <!-- 섹션 헤더: 디자인 .section { padding: 10px 8px 4px; 10px·600·uppercase·ls .06em } -->
        <div class="px-2 pt-2.5 pb-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-gray-400 dark:text-gray-600">
          {{ $t(section.labelKey) }}
        </div>
        <FolderNode
          v-for="node in section.nodes"
          :key="node.path"
          :node="node"
          :depth="0"
          :area="section.key"
          :mobile="mobile"
          :ancestors="[]"
          :selected-path="browserStore.selectedFolder?.path"
          @select="onFolderSelect"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import FolderNode from './FolderNode.vue'
import { workspaceApi } from '../api/index.js'
import { useBrowserStore } from '../stores/browser.js'
import { sessionCache } from '../utils/cache.js'

const props = defineProps({
  // 모바일 바텀시트용 — 들여쓰기 축소 + 터치 타깃 확대
  mobile: { type: Boolean, default: false },
  // 시트가 자체 헤더를 그릴 때 내부 pane 헤더를 숨긴다
  hideHeader: { type: Boolean, default: false },
})
const emit = defineEmits(['select'])

const browserStore = useBrowserStore()
const router = useRouter()
const route = useRoute()
const sections = ref([])
const loading = ref(false)

const ROOTS_TTL = 5 * 60 * 1000  // 5분
// 영역별로 캐시 키를 분리 — 단일 'roots' 키는 두 영역을 구분하지 못한다
const CACHE_KEYS = { workspace: 'roots:workspace', library: 'roots:library' }

// 루트가 없는 영역은 섹션 헤더까지 통째로 숨긴다 (빈 헤더를 남기지 않음)
const visibleSections = computed(() => sections.value.filter(s => s.nodes.length > 0))

function onFolderSelect({ node, area, crumb }) {
  // 선택된 폴더의 하위 캐시 무효화 → 외부 변경사항 즉시 반영
  sessionCache.delete(`children:${node.path}`)
  // area와 조상 체인을 명시적으로 전달한다.
  // area를 빠뜨리면 store의 `if (area)` 가드 때문에 이전 영역이 그대로 남고,
  // crumb을 빠뜨리면 breadcrumb이 이전 경로에 계속 누적된다.
  browserStore.selectFolder({ name: node.name, path: node.path }, crumb, area)
  emit('select', { node, area })
  if (route.path !== '/browser') {
    router.push('/browser')
  }
}

function toNodes(roots, area) {
  return (roots || []).map(r => ({
    name: r.name,
    path: r.path,
    has_children: r.has_children,
    isRoot: true,
    area,
  }))
}

async function loadRoots(force = false) {
  if (!force) {
    const ws = sessionCache.get(CACHE_KEYS.workspace)
    const lib = sessionCache.get(CACHE_KEYS.library)
    if (ws && lib) {
      sections.value = buildSections(ws, lib)
      return
    }
  }

  loading.value = true
  try {
    // 두 영역의 루트 API를 병합한다. /browse/roots는 ScanFolder만 읽어
    // 작업공간 루트를 반환하지 못하므로 사용하지 않는다.
    const [wsRes, libRes] = await Promise.all([
      workspaceApi.workspaceRoots().catch(() => ({ data: { roots: [] } })),
      workspaceApi.libraryRoots().catch(() => ({ data: { roots: [] } })),
    ])
    const wsNodes = toNodes(wsRes.data?.roots, 'workspace')
    const libNodes = toNodes(libRes.data?.roots, 'library')
    sessionCache.set(CACHE_KEYS.workspace, wsNodes, ROOTS_TTL)
    sessionCache.set(CACHE_KEYS.library, libNodes, ROOTS_TTL)
    sections.value = buildSections(wsNodes, libNodes)
  } catch {
    sections.value = []
  } finally {
    loading.value = false
  }
}

function buildSections(wsNodes, libNodes) {
  return [
    { key: 'workspace', labelKey: 'sidebar.workspaceSection', nodes: wsNodes },
    { key: 'library',   labelKey: 'sidebar.librarySection',   nodes: libNodes },
  ]
}

// 새로고침 버튼: 강제 재로드
async function refreshRoots() {
  sessionCache.delete(CACHE_KEYS.workspace)
  sessionCache.delete(CACHE_KEYS.library)
  sessionCache.deleteByPrefix('children:')
  await loadRoots(true)
}

onMounted(() => loadRoots())

defineExpose({ refreshRoots })
</script>
