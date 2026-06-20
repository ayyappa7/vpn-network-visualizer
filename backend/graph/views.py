from rest_framework.views import APIView
from rest_framework.response import Response
from servers.wg import get_topology


class TopologyView(APIView):
    def get(self, request):
        return Response(get_topology())