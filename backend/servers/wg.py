import re
import subprocess
import concurrent.futures
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional


def _get_setting(name, default):
    from django.conf import settings
    return getattr(settings, name, default)


@dataclass
class Peer:
    public_key: str
    endpoint: str = ''
    allowed_ips: str = ''
    last_handshake: Optional[datetime] = None
    rx_bytes: int = 0
    tx_bytes: int = 0
    persistent_keepalive: Optional[int] = None

    @property
    def primary_ip(self) -> str:
        if self.allowed_ips:
            return self.allowed_ips.split(',')[0].strip().split('/')[0]
        return ''

    @property
    def name(self) -> str:
        ip = self.primary_ip
        return ip or self.public_key[:16]

    @property
    def is_reachable(self) -> bool:
        if not self.last_handshake:
            return False
        ttl = _get_setting('HANDSHAKE_TTL', 600)
        diff = (datetime.now(timezone.utc) - self.last_handshake).total_seconds()
        return diff < ttl

    def to_dict(self):
        d = asdict(self)
        d['primary_ip'] = self.primary_ip
        d['name'] = self.name
        d['is_reachable'] = self.is_reachable
        d['last_handshake'] = self.last_handshake.isoformat() if self.last_handshake else None
        return d


def get_interface_name() -> str:
    return _get_setting('WG_INTERFACE', 'wg0')


def get_peers() -> list[Peer]:
    """Run `wg show wg0 dump` and return parsed peers."""
    try:
        result = subprocess.run(
            ["wg", "show", get_interface_name(), "dump"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return []

        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:
            return []

        peers = []
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split('\t')
            if len(parts) < 8:
                continue

            hs_ts = int(parts[4]) if parts[4] else 0
            last_hs = datetime.fromtimestamp(hs_ts, tz=timezone.utc) if hs_ts > 0 else None

            peers.append(Peer(
                public_key=parts[0],
                endpoint=parts[2],
                allowed_ips=parts[3],
                last_handshake=last_hs,
                rx_bytes=int(parts[5]) if parts[5] else 0,
                tx_bytes=int(parts[6]) if parts[6] else 0,
                persistent_keepalive=int(parts[7]) if parts[7] and parts[7].isdigit() else None,
            ))

        return peers
    except Exception as e:
        print(f"Error running wg show: {e}")
        return []


def ping_ip(ip: str, timeout: int = 3) -> Optional[float]:
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), ip],
            capture_output=True, text=True, timeout=timeout + 1
        )
        if result.returncode != 0:
            return None
        match = re.search(r'time=(\d+\.?\d*)\s*ms', result.stdout)
        return float(match.group(1)) if match else None
    except Exception:
        return None


def get_ping_results(peers: list[Peer], timeout: int = 3) -> dict[str, Optional[float]]:
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_key = {
            executor.submit(ping_ip, p.primary_ip, timeout): p.public_key
            for p in peers if p.primary_ip
        }
        for future in concurrent.futures.as_completed(future_to_key):
            pubkey = future_to_key[future]
            results[pubkey] = future.result()
    return results


def get_topology() -> dict:
    """Build graph topology from current WireGuard peers."""
    peers = get_peers()
    now = datetime.now(timezone.utc)

    nodes = [{
        'id': 'hub',
        'label': 'Monitor (Hub)',
        'type': 'hub',
        'status': 'online',
    }]

    edges = []

    for peer in peers:
        status = 'unreachable'
        if peer.is_reachable:
            status = 'reachable'
        elif peer.last_handshake:
            time_since = (now - peer.last_handshake).total_seconds()
            if time_since < 600:
                status = 'stale'

        node_id = peer.primary_ip or peer.public_key[:16]

        nodes.append({
            'id': node_id,
            'label': peer.name,
            'type': 'spoke',
            'status': status,
            'ip': peer.primary_ip,
            'public_key': peer.public_key,
            'endpoint': peer.endpoint,
            'allowed_ips': peer.allowed_ips,
            'last_handshake': peer.last_handshake.isoformat() if peer.last_handshake else None,
            'rx_bytes': peer.rx_bytes,
            'tx_bytes': peer.tx_bytes,
        })

        edges.append({
            'source': 'hub',
            'target': node_id,
            'reachable': peer.is_reachable,
        })

    return {
        'nodes': nodes,
        'edges': edges,
        'updated_at': now.isoformat(),
    }