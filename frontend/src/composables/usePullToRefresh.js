import { ref, watch, onUnmounted } from 'vue'

/**
 * 모바일 당겨서 새로고침 composable
 * @param {Ref<HTMLElement>} containerRef  - 스크롤 컨테이너 ref
 * @param {Function}         onRefresh     - 새로고침 콜백 (async 지원)
 * @param {number}           threshold     - 트리거 임계값 px (기본 65)
 */
export function usePullToRefresh(containerRef, onRefresh, threshold = 65) {
  const pulling   = ref(false)   // 현재 당기는 중
  const pullY     = ref(0)       // 당긴 거리 (px, 저항 적용 후)
  const isReady   = ref(false)   // 임계값 도달 (놓으면 실행)
  const isRefreshing = ref(false)

  let startY   = 0
  let touchEl  = null

  function onTouchStart(e) {
    if (isRefreshing.value) return
    const el = containerRef.value
    if (!el || el.scrollTop > 5) return
    startY = e.touches[0].clientY
    pulling.value = false
    pullY.value   = 0
    isReady.value = false
  }

  function onTouchMove(e) {
    if (isRefreshing.value) return
    const el = containerRef.value
    if (!el) return
    const dy = e.touches[0].clientY - startY
    if (dy <= 0 || el.scrollTop > 5) {
      if (pulling.value) { pulling.value = false; pullY.value = 0; isReady.value = false }
      return
    }
    pulling.value = true
    // 저항 계수: 처음엔 빠르게, 임계값 이후엔 느리게
    pullY.value   = Math.min(dy * 0.45, threshold + 20)
    isReady.value = pullY.value >= threshold * 0.55
  }

  function onTouchEnd() {
    if (!pulling.value) return
    if (isReady.value && !isRefreshing.value) {
      pulling.value   = false
      pullY.value     = 0
      isReady.value   = false
      isRefreshing.value = true
      Promise.resolve(onRefresh()).finally(() => {
        setTimeout(() => { isRefreshing.value = false }, 400)
      })
    } else {
      pulling.value = false
      pullY.value   = 0
      isReady.value = false
    }
  }

  function attach(el) {
    if (touchEl) detach(touchEl)
    touchEl = el
    el.addEventListener('touchstart', onTouchStart, { passive: true })
    el.addEventListener('touchmove',  onTouchMove,  { passive: true })
    el.addEventListener('touchend',   onTouchEnd,   { passive: true })
    el.addEventListener('touchcancel',onTouchEnd,   { passive: true })
  }

  function detach(el) {
    if (!el) return
    el.removeEventListener('touchstart', onTouchStart)
    el.removeEventListener('touchmove',  onTouchMove)
    el.removeEventListener('touchend',   onTouchEnd)
    el.removeEventListener('touchcancel',onTouchEnd)
  }

  const stopWatch = watch(containerRef, (el, oldEl) => {
    if (oldEl) detach(oldEl)
    if (el)    attach(el)
  }, { immediate: true })

  onUnmounted(() => {
    stopWatch()
    if (touchEl) detach(touchEl)
  })

  return { pulling, pullY, isReady, isRefreshing }
}
