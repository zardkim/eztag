/**
 * sessionStorage 기반 TTL 캐시
 * - 탭 생명주기 동안 유지 (새로고침 후에도 보존)
 * - 키 접두사: "bc:" (browse cache)
 *
 * 사용 대상:
 *   roots    : 루트 폴더 목록 (TTL 5분)
 *   children : 폴더별 하위 디렉터리 (TTL 5분)
 *
 * ── 용량 관리 ──────────────────────────────────────────────
 * sessionStorage 실측 한도는 약 5MB다. 하위 폴더 5,000개짜리 응답이
 * 709KB이므로 그런 폴더 7개면 가득 찬다.
 *
 * 예전에는 setItem 이 QuotaExceededError 를 내면 조용히 삼키기만 했고
 * 축출 정책이 없었다. 그래서 한 번 가득 차면 **그 세션 내내 캐시가
 * 전혀 동작하지 않았다** — 작은 폴더까지 포함해서, 에러도 없이.
 *
 * 지금은 두 가지로 막는다:
 *   1. MAX_ENTRY_BYTES 를 넘는 큰 응답은 애초에 저장하지 않는다.
 *      (큰 폴더 하나가 캐시 전체를 못 쓰게 만드는 것을 방지)
 *   2. 용량 초과 시 오래된 항목부터 지우고 재시도한다.
 */

const PREFIX = 'bc:'

// 단일 항목 상한. 이보다 큰 응답은 캐싱하지 않고 매번 새로 받는다.
const MAX_ENTRY_BYTES = 256 * 1024

function storageKey(key) {
  return `${PREFIX}${key}`
}

/** bc: 키들을 저장 시각(ts) 오름차순으로 반환 */
function entriesByAge() {
  const list = []
  for (const k of Object.keys(sessionStorage)) {
    if (!k.startsWith(PREFIX)) continue
    let ts = 0
    try {
      ts = JSON.parse(sessionStorage.getItem(k))?.ts ?? 0
    } catch {
      ts = 0   // 파싱 불가 항목은 가장 오래된 것으로 취급해 먼저 버린다
    }
    list.push({ key: k, ts })
  }
  return list.sort((a, b) => a.ts - b.ts)
}

export const sessionCache = {
  /**
   * 캐시에서 값을 읽음. TTL 만료 시 null 반환.
   */
  get(key) {
    try {
      const raw = sessionStorage.getItem(storageKey(key))
      if (!raw) return null
      const { data, ts, ttl } = JSON.parse(raw)
      if (Date.now() - ts > ttl) {
        sessionStorage.removeItem(storageKey(key))
        return null
      }
      return data
    } catch {
      return null
    }
  },

  /**
   * 캐시에 값 저장.
   * @param {string} key
   * @param {*} data
   * @param {number} ttl  밀리초 (기본 5분)
   * @returns {boolean} 저장 여부
   */
  set(key, data, ttl = 5 * 60 * 1000) {
    let payload
    try {
      payload = JSON.stringify({ data, ts: Date.now(), ttl })
    } catch {
      return false
    }

    // ① 너무 큰 항목은 저장하지 않는다 — 이것 하나로 캐시가 가득 차는 것을 막는다
    if (payload.length > MAX_ENTRY_BYTES) return false

    const sk = storageKey(key)
    try {
      sessionStorage.setItem(sk, payload)
      return true
    } catch {
      // ② 용량 초과 → 오래된 항목부터 지우고 재시도
      const aged = entriesByAge()
      for (const { key: old } of aged) {
        if (old === sk) continue
        try {
          sessionStorage.removeItem(old)
          sessionStorage.setItem(sk, payload)
          return true
        } catch {
          // 아직 부족하면 다음 항목을 더 지운다
        }
      }
      return false
    }
  },

  /** 특정 키 제거 */
  delete(key) {
    try {
      sessionStorage.removeItem(storageKey(key))
    } catch {}
  },

  /** 접두사 일치 키 전체 제거 */
  deleteByPrefix(prefix) {
    try {
      const fullPrefix = storageKey(prefix)
      Object.keys(sessionStorage)
        .filter(k => k.startsWith(fullPrefix))
        .forEach(k => sessionStorage.removeItem(k))
    } catch {}
  },

  /** browse 캐시 전체 제거 */
  clear() {
    try {
      Object.keys(sessionStorage)
        .filter(k => k.startsWith(PREFIX))
        .forEach(k => sessionStorage.removeItem(k))
    } catch {}
  },
}
