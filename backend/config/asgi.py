import os
import logging
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

django_asgi_app = get_asgi_application()

import servers.routing

logger = logging.getLogger(__name__)


class SchedulerASGI:
    def __init__(self, app):
        self.app = app
        self.scheduler = None

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'lifespan':
            while True:
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    await self.startup()
                    await send({'type': 'lifespan.startup.complete'})
                elif message['type'] == 'lifespan.shutdown':
                    await self.shutdown()
                    await send({'type': 'lifespan.shutdown.complete'})
                    return
            return
        await self.app(scope, receive, send)

    async def startup(self):
        from django.conf import settings
        from servers.tasks import check_handshakes
        interval = getattr(settings, 'CHECK_INTERVAL', 15)
        wg_iface = getattr(settings, 'WG_INTERFACE', 'wg0')
        ttl = getattr(settings, 'HANDSHAKE_TTL', 60)
        logger.info('Starting WireGuard handshake monitor (interval=%ss, iface=%s, ttl=%s)', interval, wg_iface, ttl)
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(
            check_handshakes,
            trigger=IntervalTrigger(seconds=interval),
            id='check_handshakes',
            replace_existing=True,
            max_instances=1,
        )
        self.scheduler.start()

    async def shutdown(self):
        if self.scheduler:
            logger.info('Shutting down scheduler...')
            self.scheduler.shutdown()


application = SchedulerASGI(ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': URLRouter(servers.routing.websocket_urlpatterns),
}))
