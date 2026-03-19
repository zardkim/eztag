import client from './index.js'

export const logsApi = {
  listScan: (params) => client.get('/logs/scan', { params }),
  clearScan: () => client.delete('/logs/scan'),
  listFiles: () => client.get('/logs/files'),
  downloadLog: (filename) => {
    const link = document.createElement('a')
    link.href = `/api/logs/download/${filename}`
    link.download = `eztag_${filename}`
    link.click()
  },
}
