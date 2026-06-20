from django.urls import path
from .views import PeerViewSet

peer_list = PeerViewSet.as_view({'get': 'list'})
peer_topology = PeerViewSet.as_view({'get': 'topology'})

urlpatterns = [
    path('', peer_list, name='peer-list'),
    path('topology/', peer_topology, name='peer-topology'),
]