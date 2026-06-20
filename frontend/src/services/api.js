import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

export function getServers() {
  return api.get('/servers/').then(r => r.data)
}

export function pingPeer(publicKey) {
  return api.post('/servers/ping/', { public_key: publicKey }).then(r => r.data)
}

