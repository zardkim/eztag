import client from './index.js'

export const configApi = {
  get: () => client.get('/config/'),
  update: (config) => client.post('/config/', { config }),
  getDestinations: () => client.get('/config/destinations'),
  addDestination: (data) => client.post('/config/destinations', data),
  deleteDestination: (index) => client.delete(`/config/destinations/${index}`),
  getWizardPresets: () => client.get('/config/wizard-presets'),
  saveWizardPresets: (presets) => client.post('/config/wizard-presets', { presets }),
}
