import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 2500,
})

export const simulationService = {
  async getStatus() {
    const { data } = await api.get('/simulation/status')
    return data
  },

  async getConfig() {
    const { data } = await api.get('/simulation/config')
    return data
  },

  async updateConfig(config) {
    const { data } = await api.post('/simulation/config', config)
    return data
  },

  async start() {
    const { data } = await api.post('/simulation/control/start')
    return data
  },

  async pause() {
    const { data } = await api.post('/simulation/control/pause')
    return data
  },

  async reset() {
    const { data } = await api.post('/simulation/control/reset')
    return data
  },
}
