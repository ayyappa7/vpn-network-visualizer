import subprocess
import re
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Server, HandshakeResult


WG_INTERFACE = getattr(settings, 'WG_INTERFACE', 'wg0')
HANDSHAKE_TTL = getattr(settings, 'HANDSHAKE_TTL', 60)


def parse_wg_endpoints():
    """Parse `wg show wg0 endpoints` to get pubkey -> IP mapping"""
    try:
        result = subprocess.run(
            ["wg", "show", WG_INTERFACE, "endpoints"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return {}
        
        endpoints = {}
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    pubkey = parts[0]
                    endpoint = parts[1]
                    ip = endpoint.split(':')[0]
                    endpoints[pubkey] = ip
        return endpoints
    except Exception as e:
        print(f"Error parsing wg endpoints: {e}")
        return {}


def parse_wg_latest_handshakes():
    """Parse `wg show wg0 latest-handshakes`"""
    try:
        result = subprocess.run(
            ["wg", "show", WG_INTERFACE, "latest-handshakes"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return {}
        
        handshakes = {}
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    pubkey = parts[0]
                    timestamp = int(parts[1])
                    handshakes[pubkey] = timestamp
        return handshakes
    except Exception as e:
        print(f"Error parsing wg handshakes: {e}")
        return {}


def parse_wg_transfer():
    """Parse `wg show wg0 transfer`"""
    try:
        result = subprocess.run(
            ["wg", "show", WG_INTERFACE, "transfer"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return {}
        
        transfers = {}
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split()
                if len(parts) >= 3:
                    pubkey = parts[0]
                    rx_bytes = int(parts[1])
                    tx_bytes = int(parts[2])
                    transfers[pubkey] = (rx_bytes, tx_bytes)
        return transfers
    except Exception as e:
        print(f"Error parsing wg transfer: {e}")
        return {}


def sync_servers_from_wg():
    """Sync Server model with WireGuard peers from `wg show`"""
    endpoints = parse_wg_endpoints()
    
    for pubkey, wg_ip in endpoints.items():
        server, created = Server.objects.get_or_create(
            wireguard_ip=wg_ip,
            defaults={
                'name': f"peer-{wg_ip.split('.')[-1]}",
                'public_key': pubkey,
                'is_active': True,
            }
        )
        if not created and server.public_key != pubkey:
            server.public_key = pubkey
            server.save(update_fields=['public_key'])
    
    return Server.objects.filter(is_active=True)


def check_handshakes():
    """Main task: check WireGuard handshakes and update database"""
    now = timezone.now()
    
    # Sync servers from WireGuard
    servers = sync_servers_from_wg()
    server_by_pubkey = {s.public_key: s for s in servers if s.public_key}
    server_by_ip = {s.wireguard_ip: s for s in servers}
    
    # Parse WireGuard data
    handshakes = parse_wg_latest_handshakes()
    transfers = parse_wg_transfer()
    
    results = []
    
    for pubkey, hs_timestamp in handshakes.items():
        server = server_by_pubkey.get(pubkey)
        if not server:
            continue
        
        last_hs = None
        if hs_timestamp > 0:
            last_hs = datetime.fromtimestamp(hs_timestamp, tz=timezone.utc)
        
        is_reachable = last_hs and (now - last_hs).total_seconds() < HANDSHAKE_TTL
        
        rx_bytes, tx_bytes = transfers.get(pubkey, (0, 0))
        
        hr = HandshakeResult.objects.create(
            server=server,
            peer_public_key=pubkey,
            last_handshake=last_hs,
            rx_bytes=rx_bytes,
            tx_bytes=tx_bytes,
            is_reachable=is_reachable,
        )
        results.append(hr)
    
    # Broadcast updates via WebSocket
    broadcast_handshake_update(results)
    
    # Cleanup old records (>1 minute)
    cleanup_old_handshakes()
    
    return results


def broadcast_handshake_update(results):
    """Send handshake updates to WebSocket clients"""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    peers_data = []
    for hr in results:
        peers_data.append({
            'peer_public_key': hr.peer_public_key,
            'peer_ip': hr.server.wireguard_ip,
            'server_name': hr.server.name,
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
    """Delete HandshakeResult older than 1 minute"""
    cutoff = timezone.now() - timezone.timedelta(minutes=1)
    HandshakeResult.objects.filter(captured_at__lt=cutoff).delete()