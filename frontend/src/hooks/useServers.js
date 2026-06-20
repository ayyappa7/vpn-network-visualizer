import { useState, useEffect, useCallback } from 'react'
import { getServers, pingPeer } from '../services/api'

export function useServers() {
  const [servers, setServers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchServers = useCallback(async () => {
    try {
      const data = await getServers()
      setServers(Array.isArray(data) ? data : data.results || [])
      setError(null)
    } catch (err) {
      setError(err.message)
    }
  }, [])

  useEffect(() => {
    setLoading(true)
    fetchServers().finally(() => setLoading(false))
  }, [fetchServers])

  const updateFromHandshake = useCallback((handshakeData) => {
    if (!handshakeData || handshakeData.type !== 'handshake.update') return
    const { peers } = handshakeData
    if (!peers) return

    setServers(prev => prev.map(s => {
      const peer = peers.find(p => p.public_key === s.public_key)
      if (peer) {
        return {
          ...s,
          last_handshake: peer.last_handshake,
          is_reachable: peer.is_reachable,
          ping_reachable: peer.ping_reachable,
          ping_latency_ms: peer.ping_latency_ms,
          rx_bytes: peer.rx_bytes,
          tx_bytes: peer.tx_bytes,
        }
      }
      return s
    }))
  }, [])

  const triggerPing = useCallback(async (publicKey) => {
    setServers(prev => prev.map(s =>
      s.public_key === publicKey ? { ...s, ping_pending: true } : s
    ))
    try {
      const result = await pingPeer(publicKey)
      setServers(prev => prev.map(s =>
        s.public_key === publicKey
          ? { ...s, ping_reachable: result.ping_reachable, ping_latency_ms: result.ping_latency_ms, ping_pending: false }
          : s
      ))
      return result
    } catch {
      setServers(prev => prev.map(s =>
        s.public_key === publicKey ? { ...s, ping_pending: false } : s
      ))
      return null
    }
  }, [])

  return { servers, loading, error, refresh: fetchServers, updateFromHandshake, triggerPing }
}