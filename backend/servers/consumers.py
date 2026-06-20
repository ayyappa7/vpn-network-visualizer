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
        
        nodes = [{
            'id': 'hub',
            'label': 'Monitor (Hub)',
            'type': 'hub',
            'status': 'online',
            'ip': '10.8.0.1',
            'public_key': '',
        }]
        
        edges = []
        
        for server in servers:
            status = 'unreachable'
            if server.handshakes.filter(is_reachable=True).exists():
                status = 'reachable'
            elif server.handshakes.exists():
                last_hs = server.handshakes.order_by('-captured_at').first()
                if last_hs and last_hs.last_handshake:
                    time_since = (timezone.now() - last_hs.last_handshake).total_seconds()
                    if time_since < 120:
                        status = 'stale'
            
            latest_hs = server.handshakes.order_by('-captured_at').first()
            
            nodes.append({
                'id': server.wireguard_ip,
                'label': server.name,
                'type': 'spoke',
                'status': status,
                'ip': server.wireguard_ip,
                'public_key': server.public_key,
                'last_handshake': latest_hs.last_handshake.isoformat() if latest_hs and latest_hs.last_handshake else None,
                'rx_bytes': latest_hs.rx_bytes if latest_hs else 0,
                'tx_bytes': latest_hs.tx_bytes if latest_hs else 0,
            })
            
            edges.append({
                'source': 'hub',
                'target': server.wireguard_ip,
                'reachable': status == 'reachable',
                'latency_estimate': None,
                'rx_bytes': latest_hs.rx_bytes if latest_hs else 0,
                'tx_bytes': latest_hs.tx_bytes if latest_hs else 0,
            })
        
        return {
            'type': 'topology',
            'nodes': nodes,
            'edges': edges,
            'updated_at': timezone.now().isoformat(),
        }

    async def send_current_topology(self):
        data = await self.get_topology_data()
        await self.send(text_data=json.dumps(data))