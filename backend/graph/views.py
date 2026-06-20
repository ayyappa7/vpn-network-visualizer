from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from servers.models import Server, HandshakeResult


class TopologyView(APIView):
    def get(self, request):
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

        return Response({
            'nodes': nodes,
            'edges': edges,
            'updated_at': now.isoformat(),
        })