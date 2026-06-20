from datetime import datetime, timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from . import wg


def check_handshakes():
    peers = wg.get_peers()
    broadcast_handshake_update(peers)
    return peers


def broadcast_handshake_update(peers):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    data = {
        'type': 'handshake.update',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'peers': [p.to_dict() for p in peers],
    }

    async_to_sync(channel_layer.group_send)("graph_updates", {
        "type": "handshake.update",
        "data": data,
    })