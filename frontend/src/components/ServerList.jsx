export default function ServerList({ servers }) {
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

  function primaryIp(server) {
    if (!server.allowed_ips) return '—'
    return server.allowed_ips.split(',')[0].trim().split('/')[0]
  }

  return (
    <div className="servers-section">
      <div className="servers-header">
        <h2>WireGuard Peers ({servers.length})</h2>
      </div>
      <table>
        <thead>
          <tr>
            <th>Peer</th>
            <th>Allowed IPs</th>
            <th>Endpoint</th>
            <th>Status</th>
            <th>Handshake</th>
            <th>Traffic</th>
          </tr>
        </thead>
        <tbody>
          {servers.map(s => (
            <tr key={s.id} className={s.is_reachable ? 'status-up' : 'status-down'}>
              <td>
                <strong>{s.name || primaryIp(s)}</strong>
                <div style={{ fontSize: '0.7rem', color: '#64748b', fontFamily: 'monospace', marginTop: 2 }}>
                  {s.public_key?.slice(0, 20)}...
                </div>
              </td>
              <td>
                <code style={{ fontSize: '0.8rem', color: '#93c5fd' }}>{s.allowed_ips || '—'}</code>
              </td>
              <td style={{ fontSize: '0.8rem', color: '#94a3b8', fontFamily: 'monospace' }}>
                {s.endpoint || '—'}
              </td>
              <td>{statusBadge(s)}</td>
              <td style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                {formatTime(s.last_handshake)}
              </td>
              <td style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#94a3b8' }}>
                {formatBytes(s.rx_bytes || 0)} ↓ / {formatBytes(s.tx_bytes || 0)} ↑
              </td>
            </tr>
          ))}
        </tbody>
      </table>
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