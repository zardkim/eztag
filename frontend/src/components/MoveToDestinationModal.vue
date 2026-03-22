<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="$emit('close')"
    >
      <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-lg mx-4 flex flex-col max-h-[85vh]">
        <!-- Header -->
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-800 shrink-0">
          <h2 class="text-base font-semibold text-gray-900 dark:text-white">{{ t('browser.moveFolder.title') }}</h2>
          <button
            class="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 p-1 rounded"
            @click="$emit('close')"
          >✕</button>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-y-auto px-5 py-4 space-y-4">

          <!-- Source folder info -->
          <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg px-3 py-2.5">
            <p class="text-xs text-blue-500 dark:text-blue-400 font-medium mb-0.5">{{ t('browser.moveFolder.sourceLabel') }}</p>
            <p class="text-sm text-blue-900 dark:text-blue-200 font-mono truncate">{{ sourceFolder }}</p>
            <p class="text-xs text-blue-400 mt-0.5">{{ t('browser.moveFolder.fileCount', { n: sourceFileCount }) }}</p>
          </div>

          <!-- No destinations registered -->
          <div v-if="destinations.length === 0 && !loadingDests" class="text-center py-4">
            <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('browser.moveFolder.noDestRegistered') }}</p>
          </div>

          <!-- Loading indicator -->
          <div v-if="loadingDests" class="text-center py-4">
            <p class="text-sm text-gray-400">로딩 중...</p>
          </div>

          <!-- Destination tree -->
          <div v-if="destinations.length > 0">
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">{{ t('browser.moveFolder.selectDest') }}</p>

            <!-- Root destination folders -->
            <div class="space-y-1">
              <div v-for="dest in destinations" :key="dest.path">
                <!-- Root node -->
                <div
                  class="flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors"
                  :class="selectedPath === dest.path
                    ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'"
                  @click="selectPath(dest.path)"
                >
                  <button
                    class="shrink-0 w-5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xs"
                    @click.stop="toggleExpand(dest.path)"
                  >{{ expandedPaths.has(dest.path) ? '▼' : '▶' }}</button>
                  <span class="text-base shrink-0">📁</span>
                  <span class="flex-1 truncate text-sm font-medium">{{ dest.label || dest.path }}</span>
                  <span class="text-xs text-gray-400 font-mono truncate max-w-[140px]" :title="dest.path">{{ shortenPath(dest.path) }}</span>
                </div>

                <!-- Children (lazy loaded) -->
                <div v-if="expandedPaths.has(dest.path)" class="ml-6 space-y-0.5 mt-0.5">
                  <div v-if="loadingChildren.has(dest.path)" class="px-3 py-1.5 text-xs text-gray-400">
                    로딩 중...
                  </div>
                  <template v-else>
                    <DestFolderNode
                      v-for="child in childrenMap[dest.path] || []"
                      :key="child.path"
                      :node="child"
                      :selected-path="selectedPath"
                      :expanded-paths="expandedPaths"
                      :loading-children="loadingChildren"
                      :children-map="childrenMap"
                      @select="selectPath"
                      @toggle="toggleExpand"
                    />
                    <div v-if="(childrenMap[dest.path] || []).length === 0" class="px-3 py-1 text-xs text-gray-400 italic">
                      빈 폴더
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>

          <!-- Selected destination display -->
          <div v-if="selectedPath" class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg px-3 py-2.5">
            <p class="text-xs text-green-500 dark:text-green-400 font-medium mb-0.5">{{ t('browser.moveFolder.selectedDest') }}</p>
            <p class="text-sm text-green-900 dark:text-green-200 font-mono truncate">{{ selectedPath }}</p>
          </div>

          <!-- Conflict warning -->
          <div v-if="hasConflict" class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg px-3 py-2 text-xs text-yellow-700 dark:text-yellow-400">
            ⚠️ {{ t('browser.moveFolder.conflictWarning') }}
          </div>

          <!-- Error -->
          <div v-if="moveError" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-3 py-2 text-xs text-red-700 dark:text-red-400">
            {{ t('browser.moveFolder.error', { error: moveError }) }}
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-end gap-3 px-5 py-4 border-t border-gray-200 dark:border-gray-800 shrink-0">
          <button
            class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            @click="$emit('close')"
          >{{ t('browser.moveFolder.cancel') }}</button>
          <button
            class="px-5 py-2 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
            :disabled="!selectedPath || moving || hasConflict"
            @click="doMove"
          >
            <span v-if="moving" class="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin"></span>
            {{ t('browser.moveFolder.move') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, h, defineComponent } from 'vue'
import { useI18n } from 'vue-i18n'
import { configApi } from '../api/config.js'
import { browseApi } from '../api/index.js'

const props = defineProps({
  sourcePath: { type: String, required: true },
  sourceFileCount: { type: Number, default: 0 },
})

const emit = defineEmits(['close', 'moved'])

const { t } = useI18n()

const sourceFolder = computed(() => {
  const parts = props.sourcePath.split('/')
  return parts[parts.length - 1] || props.sourcePath
})

function shortenPath(path) {
  if (path.length <= 30) return path
  const parts = path.split('/')
  if (parts.length <= 2) return path
  return '.../' + parts.slice(-2).join('/')
}

// Destinations
const destinations = ref([])
const loadingDests = ref(false)

// Tree state
const selectedPath = ref('')
const expandedPaths = ref(new Set())
const childrenMap = ref({})
const loadingChildren = ref(new Set())

// Move state
const moving = ref(false)
const moveError = ref('')

const hasConflict = computed(() => {
  if (!selectedPath.value) return false
  const folderName = sourceFolder.value
  const children = childrenMap.value[selectedPath.value] || []
  return children.some(c => c.name === folderName)
})

async function loadDestinations() {
  loadingDests.value = true
  try {
    const { data } = await configApi.getDestinations()
    destinations.value = data.destinations || []
  } catch (e) {
    console.error('Failed to load destinations', e)
    destinations.value = []
  } finally {
    loadingDests.value = false
  }
}

async function loadChildren(path) {
  if (loadingChildren.value.has(path)) return
  const s = new Set(loadingChildren.value)
  s.add(path)
  loadingChildren.value = s
  try {
    const { data } = await browseApi.destChildren(path)
    childrenMap.value = { ...childrenMap.value, [path]: data }
  } catch (e) {
    childrenMap.value = { ...childrenMap.value, [path]: [] }
  } finally {
    const s2 = new Set(loadingChildren.value)
    s2.delete(path)
    loadingChildren.value = s2
  }
}

async function toggleExpand(path) {
  const s = new Set(expandedPaths.value)
  if (s.has(path)) {
    s.delete(path)
  } else {
    s.add(path)
    if (!childrenMap.value[path]) {
      await loadChildren(path)
    }
  }
  expandedPaths.value = s
}

async function selectPath(path) {
  selectedPath.value = path
  moveError.value = ''
  mkdirError.value = ''
  // Pre-load children to check conflict
  if (!childrenMap.value[path]) {
    await loadChildren(path)
  }
}

async function doMove() {
  if (!selectedPath.value || moving.value) return
  moveError.value = ''
  moving.value = true
  try {
    const { data } = await browseApi.moveFolder({
      source_path: props.sourcePath,
      dest_path: selectedPath.value,
    })
    emit('moved', { dest: data.dest, tracksUpdated: data.tracks_updated })
  } catch (e) {
    if (e.response?.status === 409) {
      moveError.value = t('browser.moveFolder.conflictWarning')
    } else {
      moveError.value = e.response?.data?.detail || e.message
    }
  } finally {
    moving.value = false
  }
}

// Recursive folder tree node component
const DestFolderNode = defineComponent({
  name: 'DestFolderNode',
  props: {
    node: Object,
    selectedPath: String,
    expandedPaths: Object,
    loadingChildren: Object,
    childrenMap: Object,
  },
  emits: ['select', 'toggle'],
  setup(nodeProps, { emit: nodeEmit }) {
    return () => {
      const { node, selectedPath, expandedPaths, loadingChildren, childrenMap } = nodeProps
      const isSelected = selectedPath === node.path
      const isExpanded = expandedPaths.has(node.path)
      const isLoading = loadingChildren.has(node.path)
      const children = childrenMap[node.path] || []

      return h('div', [
        h('div', {
          class: [
            'flex items-center gap-2 px-3 py-1.5 rounded-lg cursor-pointer transition-colors text-sm',
            isSelected
              ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300'
              : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
          ].join(' '),
          onClick: () => nodeEmit('select', node.path),
        }, [
          node.has_children
            ? h('button', {
                class: 'shrink-0 w-5 text-gray-400 hover:text-gray-600 text-xs',
                onClick: (e) => { e.stopPropagation(); nodeEmit('toggle', node.path) },
              }, isExpanded ? '▼' : '▶')
            : h('span', { class: 'shrink-0 w-5' }),
          h('span', { class: 'shrink-0' }, node.has_children ? '📂' : '📁'),
          h('span', { class: 'flex-1 truncate' }, node.name),
        ]),
        isExpanded
          ? h('div', { class: 'ml-6 space-y-0.5 mt-0.5' }, [
              isLoading
                ? h('div', { class: 'px-3 py-1 text-xs text-gray-400' }, '로딩 중...')
                : children.length === 0
                  ? h('div', { class: 'px-3 py-1 text-xs text-gray-400 italic' }, '빈 폴더')
                  : children.map(child =>
                      h(DestFolderNode, {
                        key: child.path,
                        node: child,
                        selectedPath,
                        expandedPaths,
                        loadingChildren,
                        childrenMap,
                        onSelect: (p) => nodeEmit('select', p),
                        onToggle: (p) => nodeEmit('toggle', p),
                      })
                    )
            ])
          : null
      ])
    }
  }
})

onMounted(loadDestinations)
</script>
