<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-[99999] flex flex-col gap-2 pointer-events-none" style="max-width:360px; width:calc(100vw - 2rem);">
      <TransitionGroup
        enter-from-class="opacity-0 translate-x-4"
        leave-to-class="opacity-0 translate-x-4"
        enter-active-class="transition duration-200"
        leave-active-class="transition duration-150"
        move-class="transition duration-200"
      >
        <div
          v-for="toast in store.toasts"
          :key="toast.id"
          class="pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-xl shadow-xl border text-sm"
          :class="toastClass(toast.type)"
        >
          <span class="shrink-0 text-base leading-none mt-0.5">{{ toastIcon(toast.type) }}</span>
          <span class="flex-1 leading-snug whitespace-pre-line">{{ toast.message }}</span>
          <button class="shrink-0 opacity-60 hover:opacity-100 text-base leading-none" @click="store.remove(toast.id)">×</button>
        </div>
      </TransitionGroup>
    </div>

    <!-- Confirm Dialog -->
    <template v-for="c in store.confirmQueue" :key="c.id">
      <div class="fixed inset-0 bg-black/50 z-[99998] flex items-center justify-center p-4">
        <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-sm p-6">
          <h3 v-if="c.title" class="text-base font-semibold text-gray-900 dark:text-white mb-3">{{ c.title }}</h3>
          <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line">{{ c.message }}</p>
          <div class="flex justify-end gap-2 mt-5">
            <button
              class="px-4 py-2 text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
              @click="store.resolveConfirm(c.id, false)"
            >취소</button>
            <button
              class="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors"
              @click="store.resolveConfirm(c.id, true)"
            >확인</button>
          </div>
        </div>
      </div>
    </template>
  </Teleport>
</template>

<script setup>
import { useToastStore } from '../stores/toast.js'

const store = useToastStore()

function toastClass(type) {
  const map = {
    success: 'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-700 text-green-800 dark:text-green-200',
    error:   'bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-700 text-red-800 dark:text-red-200',
    warning: 'bg-amber-50 dark:bg-amber-900/30 border-amber-200 dark:border-amber-700 text-amber-800 dark:text-amber-200',
    info:    'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-700 text-blue-800 dark:text-blue-200',
  }
  return map[type] || map.info
}

function toastIcon(type) {
  const map = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' }
  return map[type] || map.info
}
</script>
