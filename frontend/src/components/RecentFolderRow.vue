<template>
  <!-- 최근 폴더 한 줄. PC 는 작업공간/라이브러리 두 칸으로 나눠 그리고
       모바일은 한 줄로 합쳐 그리므로, 행 마크업은 여기 한 곳에만 둔다. -->
  <div
    class="flex items-center gap-3 p-3.5 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm cursor-pointer hover:border-blue-300 dark:hover:border-blue-700 active:scale-[.98] transition-all"
    @click="$emit('open', item)"
  >
    <div
      class="w-10 h-10 rounded-xl flex items-center justify-center text-xl shrink-0"
      :class="item.area === 'workspace' ? 'bg-orange-100 dark:bg-orange-900/40' : item.area === 'library' ? 'bg-blue-100 dark:bg-blue-900/40' : 'bg-gray-100 dark:bg-gray-800'"
    >{{ item.area === 'workspace' ? '📂' : item.area === 'library' ? '📚' : '📁' }}</div>
    <div class="min-w-0 flex-1">
      <div class="flex items-center gap-1.5 mb-0.5">
        <span
          v-if="showBadge && item.area === 'workspace'"
          class="shrink-0 text-[10px] font-semibold px-1.5 py-0.5 rounded bg-orange-100 text-orange-600 dark:bg-orange-900/40 dark:text-orange-400"
        >WS</span>
        <span
          v-else-if="showBadge && item.area === 'library'"
          class="shrink-0 text-[10px] font-semibold px-1.5 py-0.5 rounded bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400"
        >LIB</span>
        <p class="text-sm font-medium text-gray-900 dark:text-white truncate" :title="item.path">{{ item.name }}</p>
      </div>
      <p class="text-xs text-gray-400">{{ time }}</p>
    </div>
    <svg class="w-4 h-4 text-gray-300 dark:text-gray-600 shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/>
    </svg>
  </div>
</template>

<script setup>
defineProps({
  item: { type: Object, required: true },
  time: { type: String, default: '' },
  // 영역별로 나눠 그릴 때는 열 제목이 이미 영역을 말해주므로 뱃지를 숨긴다
  showBadge: { type: Boolean, default: true },
})
defineEmits(['open'])
</script>
