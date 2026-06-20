import subprocess
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Server, HandshakeResult


WG_INTERFACE = getattr(settings, 'WG_INTERFACE', 'wg0')
HANDSHAKE_TTL = getattr(settings, 'HANDSHAKE_TTL', 60)


def parse_wg_dump():
    """Parse `wg show wg0 dump` — tab-separated, one line per peer.
    
    Line 1: interface_privkey  fwmark  listen_port
    Line 2+: peer_pubkey  preshared_key  endpoint  allowed_ips  last_handshake  rx_bytes  tx_bytes  persistent_keepalive
    """
    try:
        result = subprocess.run(
            ["wg", "show", WG_INTERFACE, "dump"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return [], []

        lines = result.stdout.strip().split('\n')
        if not lines:
            return [], []

        interface_info = lines[0].split('\t')
        peer_lines = lines[1:]

        peers = []
        for line in peer_lines:
            if not line.strip():
                continue
            parts = line.split('\t')
            if len(parts) < 8:
                continue

            pubkey = parts[0]
            endpoint = parts[2]
            allowed_ips = parts[3]
            hs_timestamp = int(parts[4]) if parts[4] else 0
            rx_bytes = int(parts[5]) if parts[5] else 0
            tx_bytes = int(parts[6]) if parts[6] else 0
            keepalive = int(parts[7]) if parts[7] else None

            last_hs = None
            if hs_timestamp > 0:
                last_hs = datetime.fromtimestamp(hs_timestamp, tz=timezone.utc)

            peers.append({
                'public_key': pubkey,
                'endpoint': endpoint,
                'allowed_ips': allowed_ips,
                'last_handshake': last_hs,
                'rx_bytes': rx_bytes,
                'tx_bytes': tx_bytes,
                'persistent_keepalive': keepalive,
            })

        return interface_info, peers
    except Exception as e:
        print(f"Error parsing wg dump: {e}")
        return [], []


def sync_servers_from_wg():
    """Sync Server model with WireGuard peers from `wg show dump`"""
    _, peers = parse_wg_dump()

    active_pubkeys = set()
    for peer in peers:
        pubkey = peer['public_key']
        active_pubkeys.add(pubkey)

        server, created = Server.objects.get_or_create(
            public_key=pubkey,
            defaults={
                'name': '',
                'endpoint': peer['endpoint'],
                'allowed_ips': peer['allowed_ips'],
                'persistent_keepalive': peer['persistent_keepalive'],
                'is_active': True,
            }
        )
        if not created:
            changed = False
            if server.endpoint != peer['endpoint']:
                server.endpoint = peer['endpoint']; changed = True
            if server.allowed_ips != peer['allowed_ips']:
                server.allowed_ips = peer['allowed_ips']; changed = True
            if server.persistent_keepalive != peer['persistent_keepalive']:
                server.persistent_keepalive = peer['persistent_keepalive']; changed = True
            if changed:
                server.save(update_fields=['endpoint', 'allowed_ips', 'persistent_keepalive', 'updated_at'])
        else:
            # Auto-generate name from first allowed IP
            ips = peer['allowed_ips'].split(',')[0].strip() if peer['allowed_ips'] else ''
            ip_part = ips.split('/')[0] if ips else ''
            if not server.name:
                server.name = ip_part or f"peer-{pubkey[:8]}"
                server.save(update_fields=['name'])

    # Deactivate servers that are no longer in WireGuard config
    Server.objects.filter(is_active=True).exclude(public_key__in=active_pubkeys).update(
        is_active=False, endpoint='', allowed_ips=''
    )
    Server.objects.filter(is_active=False, public_key__in=active_pubkeys).update(is_active=True)

    return Server.objects.filter(is_active=True)


def check_handshakes():
    """Main task: check WireGuard handshakes and update database"""
    now = timezone.now()

    servers = sync_servers_from_wg()
    server_by_pubkey = {s.public_key: s for s in servers}

    _, peers = parse_wg_dump()

    results = []
    for peer in peers:
        server = server_by_pubkey.get(peer['public_key'])
        if not server:
            continue

        is_reachable = peer['last_handshake'] and (now - peer['last_handshake']).total_seconds() < HANDSHAKE_TTL

        hr = HandshakeResult.objects.create(
            server=server,
            last_handshake=peer['last_handshake'],
            rx_bytes=peer['rx_bytes'],
            tx_bytes=peer['tx_bytes'],
            is_reachable=is_reachable,
        )
        results.append(hr)

    broadcast_handshake_update(results)
    cleanup_old_handshakes()
    return results


def broadcast_handshake_update(results):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    peers_data = []
    for hr in results:
        peers_data.append({
            'public_key': hr.server.public_key,
            'name': hr.server.name,
            'endpoint': hr.server.endpoint,
            'allowed_ips': hr.server.allowed_ips,
            'last_handshake': hr.last_handshake.isoformat() if hr.last_handshake else None,
            'rx_bytes': hr.rx_bytes,
            'tx_bytes': hr.tx_bytes,
            'is_reachable': hr.is_reachable,
            'captured_at': hr.captured_at.isoformat(),
        })

    data = {
        'type': 'handshake.update',
        'timestamp': timezone.now().isoformat(),
        'peers': peers_data,
    }

    async_to_sync(channel_layer.group_send)("graph_updates", {
        "type": "handshake.update",
        "data": data,
    })


def cleanup_old_handshakes():
    cutoff = timezone.now() - timezone.timedelta(minutes=1)
    HandshakeResult.objects.filter(captured_at__lt=cutoff).delete()