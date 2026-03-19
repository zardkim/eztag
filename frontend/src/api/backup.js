import client from './index.js'

export const backupApi = {
  status: () => client.get('/backup/status'),
  create: () => client.post('/backup/create', {}, { timeout: 300000 }),
  list: () => client.get('/backup/list'),
  download: (filename) => {
    const link = document.createElement('a')
    link.href = `/api/backup/download/${encodeURIComponent(filename)}`
    link.download = filename
    link.click()
  },
  restore: (filename) => client.post(`/backup/restore/${encodeURIComponent(filename)}`, {}, { timeout: 300000 }),
  delete: (filename) => client.delete(`/backup/${encodeURIComponent(filename)}`),
}
