import { useState } from 'react'

export default function ServerForm({ server, onSubmit, onCancel }) {
  const isEdit = !!server
  const [form, setForm] = useState({
    name: server?.name || '',
    wireguard_ip: server?.wireguard_ip || '',
    public_key: server?.public_key || '',
    public_ip: server?.public_ip || '',
    description: server?.description || '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await onSubmit(form)
      onCancel()
    } catch (err) {
      setError(err.response?.data || err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{isEdit ? 'Edit Server' : 'Add Server'}</h3>
          <button className="modal-close" onClick={onCancel}>&times;</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && (
              <div className="alert alert-info" style={{ color: '#ef4444', borderColor: '#ef4444' }}>
                {typeof error === 'string' ? error : JSON.stringify(error)}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="name">Name *</label>
              <input id="name" name="name" required
                placeholder="e.g. web-server-01"
                value={form.name} onChange={handleChange} />
            </div>

            <div className="form-group">
              <label htmlFor="wireguard_ip">WireGuard IP *</label>
              <input id="wireguard_ip" name="wireguard_ip" required
                placeholder="e.g. 10.8.0.2"
                value={form.wireguard_ip} onChange={handleChange} />
              <div className="help">VPN IP address of this server</div>
            </div>

            <div className="form-group">
              <label htmlFor="public_key">WireGuard Public Key</label>
              <input id="public_key" name="public_key"
                placeholder="e.g. xTIB...kVw="
                value={form.public_key} onChange={handleChange} />
              <div className="help">Auto-detected from wg show if left blank</div>
            </div>

            <div className="form-group">
              <label htmlFor="public_ip">Public IP (optional)</label>
              <input id="public_ip" name="public_ip"
                placeholder="e.g. 203.0.113.10"
                value={form.public_ip} onChange={handleChange} />
            </div>

            <div className="form-group">
              <label htmlFor="description">Description</label>
              <textarea id="description" name="description" rows={2}
                placeholder="Optional notes about this server"
                value={form.description} onChange={handleChange} />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-ghost" onClick={onCancel}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving...' : isEdit ? 'Update' : 'Add Server'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}