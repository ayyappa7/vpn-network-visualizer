from django.urls import path
from .views import PeerViewSet

peer_list = PeerViewSet.as_view({'get': 'list'})
peer_ping = PeerViewSet.as_view({'post': 'ping'})

urlpatterns = [
    path('', peer_list, name='peer-list'),
    path('ping/', peer_ping, name='peer-ping'),
]