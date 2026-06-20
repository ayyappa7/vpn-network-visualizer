# VPN Network Monitor

Real-time WireGuard peer monitoring with a Django + React dashboard. Uses `wg show` to track handshake status of VPN peers.

## Architecture

- **Backend**: Django 4.2 + DRF + Channels (ASGI via Daphne)
- **Frontend**: React 18 + Vite + Cytoscape.js
- **Real-time**: WebSocket via Redis channel layer
- **Scheduler**: APScheduler checks `wg show wg0` every N seconds

## Prerequisites

- Linux server with WireGuard configured (`wg0` interface)
- Docker + Docker Compose
- WireGuard peers with `PersistentKeepalive = 25` in their config

## Quick Start

```bash
# 1. Clone and start (migrations run automatically)
docker compose up -d

# 2. Access the UI
open http://<server-ip>:5173

# 3. Add your WireGuard peers via the UI
```

## Configuration

Edit `backend/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `WG_INTERFACE` | `wg0` | WireGuard interface to monitor |
| `HANDSHAKE_TTL` | `60` | Seconds since last handshake to consider peer reachable |
| `CHECK_INTERVAL` | `15` | Seconds between `wg show` checks |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection string |

## How it Works

1. APScheduler runs `wg show wg0 latest-handshakes` every 15s
2. Parses peer public keys → handshake timestamps → transfer stats
3. Auto-discovers new peers via `wg show wg0 endpoints`
4. Stores results in DB (auto-cleaned after 1 minute)
5. Broadcasts updates to all WebSocket clients
6. React renders real-time graph (green=reachable, red=unreachable)

## WireGuard Setup Template

On the monitor server's `wg0.conf`:

```ini
[Interface]
Address = 10.8.0.1/24
PrivateKey = ...

[Peer]
# Server A
PublicKey = <peer-pubkey>
AllowedIPs = 10.8.0.2/32
PersistentKeepalive = 25

[Peer]
# Server B
PublicKey = <peer-pubkey>
AllowedIPs = 10.8.0.3/32
PersistentKeepalive = 25
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

## Deployment

```bash
# Production
docker compose -f docker-compose.yml up -d --build

# View logs
docker compose logs -f backend scheduler frontend

# Create admin user (optional)
docker compose exec backend python manage.py createsuperuser
```
