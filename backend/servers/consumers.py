import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Server, HandshakeResult


class GraphConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("graph_updates", self.channel_name)
        await self.accept()
        await self.send_current_topology()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("graph_updates", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

    async def handshake_update(self, event):
        await self.send(text_data=json.dumps(event['data']))

    async def topology_update(self, event):
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def get_topology_data(self):
        servers = Server.objects.filter(is_active=True)
        now = timezone.now()

        nodes = [{
            'id': 'hub',
            'label': 'Monitor (Hub)',
            'type': 'hub',
            'status': 'online',
        }]

        edges = []

        for server in servers:
            latest_hs = server.handshakes.order_by('-captured_at').first()

            status = 'unreachable'
            if latest_hs and latest_hs.is_reachable:
                status = 'reachable'
            elif latest_hs and latest_hs.last_handshake:
                time_since = (now - latest_hs.last_handshake).total_seconds()
                if time_since < 120:
                    status = 'stale'

            ip = server.primary_ip or ''
            name = server.name or ip
            node_id = ip or server.public_key[:16]

            nodes.append({
                'id': node_id,
                'label': name,
                'type': 'spoke',
                'status': status,
                'ip': ip,
                'public_key': server.public_key,
                'endpoint': server.endpoint,
                'allowed_ips': server.allowed_ips,
                'last_handshake': latest_hs.last_handshake.isoformat() if latest_hs and latest_hs.last_handshake else None,
                'rx_bytes': latest_hs.rx_bytes if latest_hs else 0,
                'tx_bytes': latest_hs.tx_bytes if latest_hs else 0,
            })

            edges.append({
                'source': 'hub',
                'target': node_id,
                'reachable': status == 'reachable',
            })

        return {
            'type': 'topology',
            'nodes': nodes,
            'edges': edges,
            'updated_at': now.isoformat(),
        }

    async def send_current_topology(self):
        data = await self.get_topology_data()
        await self.send(text_data=json.dumps(data))