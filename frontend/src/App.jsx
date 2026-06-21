import { useEffect } from 'react'
import ServerList from './components/ServerList'
import { useServers } from './hooks/useServers'
import { useWebSocket } from './hooks/useWebSocket'

export default function App() {
  const { servers, loading, error, updateFromHandshake, triggerPing, refresh } = useServers()
  const { lastMessage, isConnected } = useWebSocket('/ws/graph/')

  useEffect(() => {
    if (lastMessage?.type === 'handshake.update') {
      updateFromHandshake(lastMessage)
    }
  }, [lastMessage, updateFromHandshake])

  return (
    <div>
      <header>
        <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1><span>VPN</span> Network Monitor</h1>
            <div className="subtitle">WireGuard Peers</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <button className="btn btn-sm btn-ghost" onClick={refresh} disabled={loading}>
              ↻ {loading ? '...' : 'Refresh'}
            </button>
            <span style={{
              display: 'inline-block',
              width: 8, height: 8,
              borderRadius: '50%',
              background: isConnected ? '#22c55e' : '#ef4444',
            }} />
            <span className="conn-status">
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
            Loading peers...
          </div>
        ) : (
          <ServerList servers={servers} onPing={triggerPing} />
        )}
      </main>
    </div>
  )
}