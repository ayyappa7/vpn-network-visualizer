import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class ServersConfig(AppConfig):
    name = 'servers'
    verbose_name = 'Servers'
    _scheduler = None

    def ready(self):
        if self.__class__._scheduler is not None:
            return
        from django.conf import settings
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        from .tasks import check_handshakes

        interval = getattr(settings, 'CHECK_INTERVAL', 15)
        wg_iface = getattr(settings, 'WG_INTERFACE', 'wg0')
        ttl = getattr(settings, 'HANDSHAKE_TTL', 600)

        scheduler = BackgroundScheduler()
        scheduler.add_job(
            check_handshakes,
            trigger=IntervalTrigger(seconds=interval),
            id='check_handshakes',
            replace_existing=True,
            max_instances=1,
        )
        scheduler.start()
        self.__class__._scheduler = scheduler
        logger.info('Started WireGuard monitor (interval=%ss, iface=%s, ttl=%s)', interval, wg_iface, ttl)
