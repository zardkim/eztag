<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      leave-active-class="transition duration-150 ease-in"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div v-if="open" class="lg:hidden fixed inset-0 z-[300] bg-black/40" @click.self="$emit('close')">
        <Transition
          enter-active-class="transition duration-200 ease-out"
          leave-active-class="transition duration-150 ease-in"
          enter-from-class="translate-y-full"
          leave-to-class="translate-y-full"
          appear
        >
          <div
            v-if="open"
            class="absolute inset-x-0 bottom-0 h-[70vh] flex flex-col bg-white dark:bg-gray-900 rounded-t-2xl shadow-2xl overflow-hidden"
            style="padding-bottom: env(safe-area-inset-bottom, 0px);"
          >
            <!-- 드래그 핸들 -->
            <div class="shrink-0 pt-2 pb-1 flex justify-center">
              <span class="w-10 h-1 rounded-full bg-gray-300 dark:bg-gray-700"></span>
            </div>

            <!-- 헤더 -->
            <div class="shrink-0 px-4 py-2 flex items-center gap-2 border-b border-gray-200 dark:border-gray-800">
              <span class="flex-1 text-sm font-semibold text-gray-900 dark:text-white">{{ $t('home.openFolder') }}</span>
              <button
                class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                :class="refreshing ? 'animate-spin' : ''"
                :title="$t('browser.refreshFolders')"
                @click="refresh"
              >
                <svg class="w-4 h-4" viewBox="0 0 16 16" fill="none">
                  <path d="M13.5 8a5.5 5.5 0 1 1-1.8-4.1" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
                  <path d="M13.5 2v3h-3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </button>
              <button
                class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                :title="$t('common.close')"
                @click="$emit('close')"
              >✕</button>
            </div>

            <!-- 트리 (자체 스크롤) -->
            <div class="flex-1 min-h-0 px-1">
              <FolderTree
                ref="treeRef"
                :mobile="true"
                :hide-header="true"
                @select="$emit('close')"
              />
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
import FolderTree from './FolderTree.vue'

defineProps({ open: { type: Boolean, default: false } })
defineEmits(['close'])

const treeRef = ref(null)
const refreshing = ref(false)

async function refresh() {
  refreshing.value = true
  try {
    await treeRef.value?.refreshRoots()
  } finally {
    refreshing.value = false
  }
}
</script>
