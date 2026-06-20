from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .wg import get_peers, ping_ip


class PeerViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    def list(self, request):
        peers = get_peers()
        return Response([p.to_dict() for p in peers])

    @action(detail=False, methods=['post'])
    def ping(self, request):
        public_key = request.data.get('public_key')
        if not public_key:
            return Response({'error': 'public_key required'}, status=status.HTTP_400_BAD_REQUEST)
        peers = get_peers()
        peer = next((p for p in peers if p.public_key == public_key), None)
        if not peer:
            return Response({'error': 'peer not found'}, status=status.HTTP_404_NOT_FOUND)
        if not peer.primary_ip:
            return Response({'error': 'no IP to ping'}, status=status.HTTP_400_BAD_REQUEST)
        latency = ping_ip(peer.primary_ip)
        return Response({
            'public_key': public_key,
            'ip': peer.primary_ip,
            'ping_reachable': latency is not None,
            'ping_latency_ms': latency,
        })