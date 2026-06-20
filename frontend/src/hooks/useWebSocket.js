import { useEffect, useRef, useState, useCallback } from 'react'

const WS_BASE = import.meta.env.VITE_WS_URL || ''

export function useWebSocket(path) {
  const [lastMessage, setLastMessage] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const mountedRef = useRef(true)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = WS_BASE || `${protocol}//${window.location.host}`
    const url = `${host}${path}`

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      if (mountedRef.current) setIsConnected(true)
    }

    ws.onmessage = (event) => {
      if (mountedRef.current) {
        try {
          setLastMessage(JSON.parse(event.data))
        } catch {
          setLastMessage({ type: 'raw', data: event.data })
        }
      }
    }

    ws.onclose = () => {
      if (mountedRef.current) {
        setIsConnected(false)
        reconnectTimeoutRef.current = setTimeout(connect, 3000)
      }
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [path])

  useEffect(() => {
    mountedRef.current = true
    connect()

    return () => {
      mountedRef.current = false
      clearTimeout(reconnectTimeoutRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { lastMessage, isConnected }
}