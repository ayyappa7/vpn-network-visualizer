from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Subquery, OuterRef
from django.utils import timezone
from .models import Server, HandshakeResult
from .serializers import ServerSerializer, HandshakeResultSerializer


class ServerViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Server.objects.filter(is_active=True)
    serializer_class = ServerSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        latest = HandshakeResult.objects.filter(
            server=OuterRef('pk')
        ).order_by('-captured_at')
        return queryset.annotate(
            last_handshake=Subquery(latest.values('last_handshake')[:1]),
            rx_bytes=Subquery(latest.values('rx_bytes')[:1]),
            tx_bytes=Subquery(latest.values('tx_bytes')[:1]),
        )

    @action(detail=False, methods=['get'])
    def topology(self, request):
        servers = self.get_queryset()
        now = timezone.now()

        nodes = [{
            'id': 'hub',
            'label': 'Monitor (Hub)',
            'type': 'hub',
            'status': 'online',
        }]

        edges = []

        for server in servers:
            status = 'unreachable'
            if server.is_reachable:
                status = 'reachable'
            elif hasattr(server, 'last_handshake') and server.last_handshake:
                time_since = (now - server.last_handshake).total_seconds()
                if time_since < 120:
                    status = 'stale'

            ip = server.primary_ip or ''
            name = server.name or ip

            nodes.append({
                'id': ip or server.public_key[:16],
                'label': name,
                'type': 'spoke',
                'status': status,
                'ip': ip,
                'public_key': server.public_key,
                'endpoint': server.endpoint,
                'allowed_ips': server.allowed_ips,
                'last_handshake': getattr(server, 'last_handshake', None),
                'rx_bytes': getattr(server, 'rx_bytes', 0) or 0,
                'tx_bytes': getattr(server, 'tx_bytes', 0) or 0,
            })

            edges.append({
                'source': 'hub',
                'target': ip or server.public_key[:16],
                'reachable': status == 'reachable',
            })

        return Response({
            'nodes': nodes,
            'edges': edges,
            'updated_at': now.isoformat(),
        })


class HandshakeResultViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = HandshakeResult.objects.all()
    serializer_class = HandshakeResultSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        server_id = self.request.query_params.get('server')
        if server_id:
            qs = qs.filter(server_id=server_id)
        return qs.order_by('-captured_at')[:100]