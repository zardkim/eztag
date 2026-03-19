/**
 * Blob 데이터를 파일로 다운로드.
 * @param {Blob} blob - 다운로드할 Blob 객체
 * @param {string} filename - 저장할 파일명
 */
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.style.display = 'none'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(url), 5000)
}
