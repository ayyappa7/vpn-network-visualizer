import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

export function getServers() {
  return api.get('/servers/').then(r => r.data)
}

