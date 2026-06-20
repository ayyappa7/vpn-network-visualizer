import { useEffect } from 'react'
import GraphView from './components/GraphView'
import ServerList from './components/ServerList'
import { useServers } from './hooks/useServers'
import { useWebSocket } from './hooks/useWebSocket'

export default function App() {
  const { servers, topology, loading, error, updateFromHandshake, refresh } = useServers()
  const { lastMessage, isConnected } = useWebSocket('/ws/graph/')

  useEffect(() => {
    if (lastMessage?.type === 'handshake.update') {
      updateFromHandshake(lastMessage)
    } else if (lastMessage?.type === 'topology') {
      refresh()
    }
  }, [lastMessage, updateFromHandshake, refresh])

  return (
    <div>
      <header>
        <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1><span>VPN</span> Network Monitor</h1>
            <div className="subtitle">WireGuard Hub-Spoke Topology</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{
              display: 'inline-block',
              width: 8, height: 8,
              borderRadius: '50%',
              background: isConnected ? '#22c55e' : '#ef4444',
            }} />
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              {isConnected ? 'Connected' : 'Reconnecting...'}
            </span>
          </div>
        </div>
      </header>

      <main className="container">
        {error && (
          <div className="alert alert-info" style={{ color: '#ef4444', borderColor: '#ef4444' }}>
            Error: {error}
          </div>
        )}

        {loading ? (
          <div className="loading">
            <div className="spinner" />
            Loading network topology...
          </div>
        ) : (
          <>
            <GraphView topology={topology} />
            <ServerList servers={servers} />
          </>
        )}
      </main>
    </div>
  )
}