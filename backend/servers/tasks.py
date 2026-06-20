from datetime import datetime, timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from . import wg


def check_handshakes():
    peers = wg.get_peers()
    ping_results = wg.get_ping_results(peers)
    enriched = []
    for p in peers:
        d = p.to_dict()
        latency = ping_results.get(p.public_key)
        d['ping_latency_ms'] = latency
        d['ping_reachable'] = latency is not None
        enriched.append(d)
    broadcast_handshake_update(enriched)
    return enriched


def broadcast_handshake_update(peers_data):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    data = {
        'type': 'handshake.update',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'peers': peers_data,
    }

    async_to_sync(channel_layer.group_send)("graph_updates", {
        "type": "handshake.update",
        "data": data,
    })