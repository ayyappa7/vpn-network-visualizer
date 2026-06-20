import { useEffect, useRef } from 'react'

export default function GraphView({ topology }) {
  const containerRef = useRef(null)
  const cyRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current) return

    async function initCytoscape() {
      const cytoscape = (await import('cytoscape')).default
      const coseBilkent = (await import('cytoscape-cose-bilkent')).default
      cytoscape.use(coseBilkent)

      cyRef.current = cytoscape({
        container: containerRef.current,
        style: [
          {
            selector: 'node[type="hub"]',
            style: {
              'background-color': '#3b82f6',
              label: 'data(label)',
              'font-size': '14px',
              'font-weight': 'bold',
              'text-valign': 'bottom',
              'text-halign': 'center',
              'text-margin-y': 8,
              width: 60,
              height: 60,
              'border-width': 3,
              'border-color': '#1d4ed8',
              color: '#e2e8f0',
            },
          },
          {
            selector: 'node[type="spoke"]',
            style: {
              'background-color': '#64748b',
              label: 'data(label)',
              'font-size': '12px',
              'text-valign': 'bottom',
              'text-halign': 'center',
              'text-margin-y': 6,
              width: 45,
              height: 45,
              'border-width': 3,
              'border-color': '#475569',
              color: '#e2e8f0',
            },
          },
          {
            selector: 'node[status="reachable"]',
            style: {
              'background-color': '#22c55e',
              'border-color': '#16a34a',
            },
          },
          {
            selector: 'node[status="stale"]',
            style: {
              'background-color': '#eab308',
              'border-color': '#ca8a04',
            },
          },
          {
            selector: 'node[status="unreachable"]',
            style: {
              'background-color': '#ef4444',
              'border-color': '#dc2626',
            },
          },
          {
            selector: 'node[label]',
            style: {
              color: '#f1f5f9',
              'text-outline-width': 2,
              'text-outline-color': '#0f172a',
            },
          },
          {
            selector: 'edge',
            style: {
              width: 2,
              'line-color': '#64748b',
              'target-arrow-color': '#64748b',
              'target-arrow-shape': 'triangle',
              'curve-style': 'bezier',
            },
          },
          {
            selector: 'edge[reachable="true"]',
            style: {
              'line-color': '#22c55e',
              'target-arrow-color': '#22c55e',
              width: 3,
            },
          },
          {
            selector: 'edge[reachable="false"]',
            style: {
              'line-color': '#ef4444',
              'target-arrow-color': '#ef4444',
              width: 2,
              'line-style': 'dashed',
            },
          },
        ],
        layout: {
          name: 'cose-bilkent',
          animate: true,
          animationDuration: 500,
          nodeRepulsion: 8000,
          idealEdgeLength: 200,
          gravity: 1,
          numIter: 1000,
        },
        userZoomingEnabled: true,
        userPanningEnabled: true,
        boxSelectionEnabled: false,
      })

      cyRef.current.on('tap', 'node', (evt) => {
        const node = evt.target
        const data = node.data()

        if (data.type === 'hub') {
          console.log('Hub node clicked')
          return
        }

        let info = `${data.label}\n`
        info += `Status: ${data.status}\n`
        if (data.allowed_ips) info += `Allowed IPs: ${data.allowed_ips}\n`
        if (data.endpoint) info += `Endpoint: ${data.endpoint}\n`
        if (data.last_handshake) {
          const time = new Date(data.last_handshake).toLocaleTimeString()
          info += `Last handshake: ${time}\n`
        }
        info += `RX: ${formatBytes(data.rx_bytes || 0)}  TX: ${formatBytes(data.tx_bytes || 0)}`

        const tooltip = document.createElement('div')
        tooltip.style.cssText = `
          position: fixed; background: #1e293b; border: 1px solid #475569;
          border-radius: 8px; padding: 12px 16px; color: #e2e8f0;
          font-size: 13px; white-space: pre-line; z-index: 1000;
          box-shadow: 0 4px 12px rgba(0,0,0,0.4);
          pointer-events: none;
        `
        tooltip.textContent = info
        document.body.appendChild(tooltip)

        const move = (e) => {
          tooltip.style.left = (e.clientX + 12) + 'px'
          tooltip.style.top = (e.clientY + 12) + 'px'
        }
        document.addEventListener('mousemove', move)

        setTimeout(() => {
          document.removeEventListener('mousemove', move)
          tooltip.remove()
        }, 3000)
      })
    }

    initCytoscape()

    return () => {
      cyRef.current?.destroy()
    }
  }, [])

  useEffect(() => {
    if (!cyRef.current || !topology) return
    const cy = cyRef.current

    const elements = [
      ...topology.nodes.map(n => ({
        group: 'nodes',
        data: {
          id: n.id,
          label: n.label,
          type: n.type,
          status: n.status,
          ip: n.ip,
          public_key: n.public_key,
          endpoint: n.endpoint,
          allowed_ips: n.allowed_ips,
          last_handshake: n.last_handshake,
          rx_bytes: n.rx_bytes,
          tx_bytes: n.tx_bytes,
        },
      })),
      ...topology.edges.map(e => ({
        group: 'edges',
        data: {
          id: `${e.source}-${e.target}`,
          source: e.source,
          target: e.target,
          reachable: e.reachable,
        },
      })),
    ]

    cy.json({ elements })
    cy.layout({ name: 'cose-bilkent', animate: true, animationDuration: 500 }).run()
    cy.fit(undefined, 40)
  }, [topology])

  return (
    <div className="graph-container">
      <div className="graph-toolbar">
        <span className="title">Network Topology</span>
        <div className="status-bar">
          <span><span className="dot green"></span>Reachable</span>
          <span><span className="dot yellow"></span>Stale</span>
          <span><span className="dot red"></span>Unreachable</span>
          {topology?.updated_at && (
            <span style={{ color: '#64748b' }}>
              Updated: {new Date(topology.updated_at).toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>
      <div id="cy" ref={containerRef} />
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