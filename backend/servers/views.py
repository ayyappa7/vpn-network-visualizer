from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from .wg import get_peers, get_ping_results, get_topology


class PeerViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    def list(self, request):
        peers = get_peers()
        ping_results = get_ping_results(peers)
        data = []
        for p in peers:
            d = p.to_dict()
            d['ping_reachable'] = ping_results.get(p.public_key)
            data.append(d)
        return Response(data)

    @action(detail=False, methods=['get'])
    def topology(self, request):
        return Response(get_topology())