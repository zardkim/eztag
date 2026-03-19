import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])
  const confirmQueue = ref([])
  let nextId = 0

  function add(message, type = 'info', duration = 3000) {
    const id = ++nextId
    toasts.value.push({ id, message, type })
    if (duration > 0) setTimeout(() => remove(id), duration)
    return id
  }
  function remove(id) {
    const idx = toasts.value.findIndex(t => t.id === id)
    if (idx >= 0) toasts.value.splice(idx, 1)
  }
  function success(msg, duration = 3000) { return add(msg, 'success', duration) }
  function error(msg, duration = 5000) { return add(msg, 'error', duration) }
  function warning(msg, duration = 4000) { return add(msg, 'warning', duration) }
  function info(msg, duration = 3000) { return add(msg, 'info', duration) }

  // Promise-based confirm
  function confirm(message, title = '') {
    return new Promise((resolve) => {
      const id = ++nextId
      confirmQueue.value.push({ id, message, title, resolve })
    })
  }
  function resolveConfirm(id, result) {
    const idx = confirmQueue.value.findIndex(c => c.id === id)
    if (idx >= 0) {
      confirmQueue.value[idx].resolve(result)
      confirmQueue.value.splice(idx, 1)
    }
  }

  return { toasts, confirmQueue, add, remove, success, error, warning, info, confirm, resolveConfirm }
})
