from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from .wg import get_peers, get_topology


class PeerViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    def list(self, request):
        peers = get_peers()
        return Response([p.to_dict() for p in peers])

    @action(detail=False, methods=['get'])
    def topology(self, request):
        return Response(get_topology())