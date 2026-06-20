from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServerViewSet, HandshakeResultViewSet

router = DefaultRouter()
router.register(r'', ServerViewSet, basename='server')
router.register(r'handshakes', HandshakeResultViewSet, basename='handshake')

urlpatterns = [
    path('', include(router.urls)),
]