<template>
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1.5 sm:gap-4">
    <div class="min-w-0">
      <p class="text-sm text-gray-900 dark:text-white">{{ label }}</p>
      <p v-if="desc" class="text-xs text-gray-500 mt-0.5">{{ desc }}</p>
    </div>
    <div class="sm:shrink-0">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({ label: String, desc: String })
</script>
