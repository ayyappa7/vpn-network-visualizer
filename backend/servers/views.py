from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Subquery, OuterRef
from django.utils import timezone
from .models import Server, HandshakeResult
from .serializers import ServerSerializer, ServerListSerializer, HandshakeResultSerializer


class ServerViewSet(viewsets.ModelViewSet):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return ServerListSerializer
        return ServerSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        latest_handshake = HandshakeResult.objects.filter(
            server=OuterRef('pk')
        ).order_by('-captured_at')
        return queryset.annotate(
            last_handshake=Subquery(latest_handshake.values('last_handshake')[:1]),
            rx_bytes=Subquery(latest_handshake.values('rx_bytes')[:1]),
            tx_bytes=Subquery(latest_handshake.values('tx_bytes')[:1]),
        )

    @action(detail=False, methods=['get'])
    def topology(self, request):
        """Get graph topology data for visualization"""
        servers = self.get_queryset()
        
        nodes = []
        edges = []
        
        # Hub node (monitor itself)
        nodes.append({
            'id': 'hub',
            'label': 'Monitor (Hub)',
            'type': 'hub',
            'status': 'online',
            'ip': '10.8.0.1',
            'public_key': '',
        })
        
        for server in servers:
            status = 'unreachable'
            if server.is_reachable:
                status = 'reachable'
            elif server.last_handshake:
                time_since = (timezone.now() - server.last_handshake).total_seconds()
                if time_since < 120:
                    status = 'stale'
            
            nodes.append({
                'id': server.wireguard_ip,
                'label': server.name,
                'type': 'spoke',
                'status': status,
                'ip': server.wireguard_ip,
                'public_key': server.public_key,
                'last_handshake': server.last_handshake.isoformat() if server.last_handshake else None,
                'rx_bytes': server.rx_bytes or 0,
                'tx_bytes': server.tx_bytes or 0,
            })
            
            edges.append({
                'source': 'hub',
                'target': server.wireguard_ip,
                'reachable': server.is_reachable,
                'latency_estimate': None,
                'rx_bytes': server.rx_bytes or 0,
                'tx_bytes': server.tx_bytes or 0,
            })
        
        return Response({
            'nodes': nodes,
            'edges': edges,
            'updated_at': timezone.now().isoformat(),
        })


class HandshakeResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HandshakeResult.objects.all()
    serializer_class = HandshakeResultSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        server_id = self.request.query_params.get('server')
        if server_id:
            queryset = queryset.filter(server_id=server_id)
        return queryset.order_by('-captured_at')[:100]