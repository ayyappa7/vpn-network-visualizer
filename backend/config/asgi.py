import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import servers.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            servers.routing.websocket_urlpatterns
        )
    ),
})