/**
 * sessionStorage 기반 TTL 캐시
 * - 탭 생명주기 동안 유지 (새로고침 후에도 보존)
 * - 키 접두사: "bc:" (browse cache)
 *
 * 사용 대상:
 *   roots    : 루트 폴더 목록 (TTL 5분)
 *   children : 폴더별 하위 디렉터리 (TTL 5분)
 */

const PREFIX = 'bc:'

function storageKey(key) {
  return `${PREFIX}${key}`
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
   */
  set(key, data, ttl = 5 * 60 * 1000) {
    try {
      sessionStorage.setItem(storageKey(key), JSON.stringify({ data, ts: Date.now(), ttl }))
    } catch {
      // sessionStorage 용량 초과 시 무시
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
