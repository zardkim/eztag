/**
 * 태그 값에 파일명 금지 특수문자가 포함되어 있는지 감지.
 * 태그 저장 자체는 허용하되 사용자에게 안내할 때 사용.
 *
 * 대상 문자:
 *   ASCII 금지:  \ / : * ? " < > |
 *   전각 대응:   ＊ ／ ： ＜ ＞ ？ ＼
 *   Division Slash 계열: ∕ ∖ ⧵
 */
const FILENAME_SPECIAL_RE = /[\\/:*?"<>|\uff0a\uff0f\uff1a\uff1c\uff1e\uff1f\uff3c\u2215\u2216\u29f5]/

/**
 * 주어진 문자열에 파일명 금지 특수문자가 포함되어 있는지 반환.
 * @param {string} value
 * @returns {boolean}
 */
export function hasFilenameSpecialChars(value) {
  return value ? FILENAME_SPECIAL_RE.test(value) : false
}

/**
 * 여러 필드 값 중 하나라도 파일명 금지 특수문자가 있는지 확인.
 * @param {Record<string, string>} fields  { fieldName: value }
 * @returns {boolean}
 */
export function hasAnyFilenameSpecialChars(fields) {
  return Object.values(fields).some(v => hasFilenameSpecialChars(v))
}
