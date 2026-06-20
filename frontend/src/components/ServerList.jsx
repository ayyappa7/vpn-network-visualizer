import { useState } from 'react'
import ServerForm from './ServerForm'

export default function ServerList({ servers, onAdd, onEdit, onDelete }) {
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)

  function formatTime(iso) {
    if (!iso) return 'Never'
    const diff = Date.now() - new Date(iso).getTime()
    const secs = Math.floor(diff / 1000)
    if (secs < 10) return 'Just now'
    if (secs < 60) return `${secs}s ago`
    const mins = Math.floor(secs / 60)
    return `${mins}m ago`
  }

  function statusBadge(server) {
    if (server.is_reachable === true) {
      return <span className="badge badge-success">🟢 Reachable</span>
    }
    if (server.last_handshake) {
      return <span className="badge badge-warning">🟡 Stale</span>
    }
    return <span className="badge badge-danger">🔴 Unreachable</span>
  }

  return (
    <div className="servers-section">
      <div className="servers-header">
        <h2>Servers ({servers.length})</h2>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          + Add Server
        </button>
      </div>

      {servers.length === 0 ? (
        <div className="empty-state">
          <h3>No servers configured</h3>
          <p>Add your WireGuard peer servers to start monitoring.</p>
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>WireGuard IP</th>
              <th>Public Key</th>
              <th>Status</th>
              <th>Last Handshake</th>
              <th>Traffic</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {servers.map(s => (
              <tr key={s.id} className={s.is_reachable ? 'status-up' : 'status-down'}>
                <td><strong>{s.name}</strong></td>
                <td style={{ fontFamily: 'monospace' }}>{s.wireguard_ip}</td>
                <td style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#94a3b8' }}>
                  {s.public_key ? s.public_key.substring(0, 20) + '...' : '—'}
                </td>
                <td>{statusBadge(s)}</td>
                <td style={{ color: '#94a3b8', fontSize: '0.75rem' }}>
                  {formatTime(s.last_handshake)}
                </td>
                <td style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#94a3b8' }}>
                  {formatBytes(s.rx_bytes || 0)} / {formatBytes(s.tx_bytes || 0)}
                </td>
                <td>
                  <button className="btn btn-sm btn-ghost" onClick={() => setEditing(s)}
                    style={{ marginRight: 4 }}>
                    Edit
                  </button>
                  <button className="btn btn-sm btn-danger" onClick={() => {
                    if (confirm(`Delete ${s.name}?`)) onDelete(s.id)
                  }}>
                    Del
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {showForm && (
        <ServerForm
          onSubmit={onAdd}
          onCancel={() => setShowForm(false)}
        />
      )}

      {editing && (
        <ServerForm
          server={editing}
          onSubmit={(data) => onEdit(editing.id, data)}
          onCancel={() => setEditing(null)}
        />
      )}
    </div>
  )
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}