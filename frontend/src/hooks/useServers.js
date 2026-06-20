import { useState, useEffect, useCallback } from 'react'
import { getServers, getTopology } from '../services/api'

export function useServers() {
  const [servers, setServers] = useState([])
  const [topology, setTopology] = useState(null)
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

  const fetchTopology = useCallback(async () => {
    try {
      const data = await getTopology()
      setTopology(data)
    } catch (err) {
      console.error('Failed to fetch topology:', err)
    }
  }, [])

  useEffect(() => {
    setLoading(true)
    Promise.all([fetchServers(), fetchTopology()]).finally(() => setLoading(false))
  }, [fetchServers, fetchTopology])

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
          rx_bytes: peer.rx_bytes,
          tx_bytes: peer.tx_bytes,
        }
      }
      return s
    }))

    setTopology(prev => {
      if (!prev) return prev
      const peerMap = {}
      for (const peer of peers) {
        const ip = peer.allowed_ips?.split(',')[0]?.trim()?.split('/')[0] || peer.public_key?.slice(0, 16)
        peerMap[ip] = {
          status: peer.is_reachable ? 'reachable' : 'unreachable',
          last_handshake: peer.last_handshake,
          rx_bytes: peer.rx_bytes,
          tx_bytes: peer.tx_bytes,
        }
      }
      return {
        ...prev,
        updated_at: handshakeData.timestamp,
        nodes: prev.nodes.map(n => {
          if (n.type === 'spoke' && peerMap[n.ip || n.id]) {
            return { ...n, ...peerMap[n.ip || n.id] }
          }
          return n
        }),
        edges: prev.edges.map(e => {
          if (peerMap[e.target]) {
            return { ...e, reachable: peerMap[e.target].status === 'reachable' }
          }
          return e
        }),
      }
    })
  }, [])

  return { servers, topology, loading, error, refresh: fetchServers, updateFromHandshake }
}