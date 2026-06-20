import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  headers: { 'Content-Type': 'application/json' },
})

export function getServers() {
  return api.get('/servers/').then(r => r.data)
}

export function getServer(id) {
  return api.get(`/servers/${id}/`).then(r => r.data)
}

export function createServer(data) {
  return api.post('/servers/', data).then(r => r.data)
}

export function updateServer(id, data) {
  return api.put(`/servers/${id}/`, data).then(r => r.data)
}

export function deleteServer(id) {
  return api.delete(`/servers/${id}/`).then(r => r.data)
}

export function getTopology() {
  return api.get('/graph/topology/').then(r => r.data)
}