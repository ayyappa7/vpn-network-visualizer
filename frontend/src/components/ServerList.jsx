export default function ServerList({ servers, onPing }) {
  if (servers.length === 0) {
    return (
      <div className="servers-section">
        <div className="servers-header">
          <h2>WireGuard Peers</h2>
        </div>
        <div className="empty-state">
          <h3>No peers detected</h3>
          <p>Waiting for WireGuard handshake data from <code>wg show</code>...</p>
        </div>
      </div>
    )
  }

  function formatTime(iso) {
    if (!iso) return '—'
    const diff = Date.now() - new Date(iso).getTime()
    const secs = Math.floor(diff / 1000)
    if (secs < 10) return 'Just now'
    if (secs < 60) return `${secs}s ago`
    const mins = Math.floor(secs / 60)
    return `${mins}m ago`
  }

  function statusBadge(server) {
    if (server.is_reachable === true) return <span className="badge badge-success">Reachable</span>
    if (server.last_handshake) return <span className="badge badge-warning">Stale</span>
    return <span className="badge badge-danger">Unreachable</span>
  }

  function pingBadge(server) {
    if (server.ping_pending) return <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>pinging...</span>
    if (server.ping_latency_ms !== undefined && server.ping_latency_ms !== null) {
      const ms = server.ping_latency_ms.toFixed(1)
      const color = ms < 50 ? '#22c55e' : ms < 150 ? '#eab308' : '#ef4444'
      return <span style={{ fontFamily: 'monospace', fontSize: '0.8rem', color }}>{ms}ms</span>
    }
    if (server.ping_reachable === false) return <span className="badge badge-danger">Timeout</span>
    return <span style={{ fontSize: '0.75rem', color: '#64748b' }}>—</span>
  }

  function primaryIp(server) {
    if (!server.allowed_ips) return '—'
    return server.allowed_ips.split(',')[0].trim().split('/')[0]
  }

  return (
    <div className="servers-section">
      <div className="servers-header">
        <h2>WireGuard Peers ({servers.length})</h2>
      </div>
      <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Peer</th>
            <th className="hide-mobile">Allowed IPs</th>
            <th className="hide-mobile">Endpoint</th>
            <th>Status</th>
            <th>Handshake</th>
            <th>Ping</th>
            <th></th>
            <th className="hide-mobile">Traffic</th>
          </tr>
        </thead>
        <tbody>
            {servers.map(s => (
            <tr key={s.public_key} className={s.is_reachable ? 'status-up' : 'status-down'}>
              <td>
                <strong>{s.name || primaryIp(s)}</strong>
                <div className="pubkey-hint">
                  {s.public_key?.slice(0, 20)}...
                </div>
              </td>
              <td className="hide-mobile">
                <code className="ip-code">{s.allowed_ips || '—'}</code>
              </td>
              <td className="hide-mobile ep-cell">
                {s.endpoint || '—'}
              </td>
              <td>{statusBadge(s)}</td>
              <td className="hs-cell">
                {formatTime(s.last_handshake)}
              </td>
              <td>{pingBadge(s)}</td>
              <td>
                <button
                  className="btn btn-sm btn-primary"
                  onClick={() => onPing?.(s.public_key)}
                  disabled={s.ping_pending}
                >
                  {s.ping_pending ? '...' : 'Ping'}
                </button>
              </td>
              <td className="hide-mobile traffic-cell">
                {formatBytes(s.rx_bytes || 0)} ↓ / {formatBytes(s.tx_bytes || 0)} ↑
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
      <div style={{ padding: '12px 16px', fontSize: '0.8rem', color: '#64748b', borderTop: '1px solid #334155' }}>
        Auto-detected from <code>$ wg show wg0 dump</code> &middot; Updates every 15s
      </div>
    </div>
  )
}

function formatBytes(bytes) {
  if (bytes === 0) return '0'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}