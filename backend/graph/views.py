from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from servers.models import Server, HandshakeResult


class TopologyView(APIView):
    def get(self, request):
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
            latest_hs = server.handshakes.order_by('-captured_at').first()
            
            status = 'unreachable'
            if latest_hs and latest_hs.is_reachable:
                status = 'reachable'
            elif latest_hs and latest_hs.last_handshake:
                time_since = (timezone.now() - latest_hs.last_handshake).total_seconds()
                if time_since < 120:
                    status = 'stale'
            
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
        
        return Response({
            'nodes': nodes,
            'edges': edges,
            'updated_at': timezone.now().isoformat(),
        })