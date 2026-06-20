# VPN Network Monitor

Real-time WireGuard peer monitoring via `wg show wg0`. Shows hub-spoke topology with reachability status.

## Stack
- **Backend**: Django 4.2 + DRF + Channels (Daphne ASGI)
- **Frontend**: React 18 + Vite + Cytoscape.js
- **Real-time**: WebSocket via Redis channel layer
- **Scheduler**: APScheduler checks `wg show` every 15s

## Architecture

```
Browser → http://server:5173
              │
          Vite (host networking)
          ├── /api/* → proxy → localhost:8000 (Daphne)
          └── /ws/*  → proxy → localhost:8000 (Daphne)
                                  │
                           Backend (host networking)
                           ├── Daphne ASGI server
                           ├── APScheduler (wg show)
                           └── Redis channel layer
```

All services use `network_mode: host` for direct `wg` command access.

## Quick Start

```bash
# On your WireGuard hub server:
git clone <repo>
cd vpn-monitor

# Build and start
docker compose up -d --build

# Open browser
open http://<server-ip>:5173

# Add your peers via the UI
```

## Adding a Peer

1. Open the web UI
2. Click "+ Add Server"
3. Enter:
   - **Name**: e.g. `web-01`
   - **WireGuard IP**: e.g. `10.8.0.2`
   - **Public Key**: Optional (auto-detected from `wg show`)

## Troubleshooting

```bash
# Check backend logs
docker compose logs backend

# Check scheduler logs
docker compose logs scheduler

# Test API directly
curl http://localhost:8000/api/servers/
curl http://localhost:8000/api/graph/topology/

# Check WireGuard is accessible
docker compose exec backend wg show wg0 latest-handshakes

# Frontend at http://server-ip:5173
# API at http://server-ip:8000/api/
# WebSocket at ws://server-ip:8000/ws/graph/
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/servers/` | List servers |
| POST | `/api/servers/` | Add server |
| GET | `/api/servers/{id}/` | Server detail |
| PUT | `/api/servers/{id}/` | Update server |
| DELETE | `/api/servers/{id}/` | Delete server |
| GET | `/api/graph/topology/` | Graph data |
| WS | `/ws/graph/` | Real-time updates |

## Configuration

Edit `backend/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `WG_INTERFACE` | `wg0` | WireGuard interface to monitor |
| `HANDSHAKE_TTL` | `60` | Seconds since last handshake to consider peer reachable |
| `CHECK_INTERVAL` | `15` | Seconds between `wg show` checks |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection string |
