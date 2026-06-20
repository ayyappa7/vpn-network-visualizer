import time
import logging
from django.core.management.base import BaseCommand
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings
from servers.tasks import check_handshakes

logger = logging.getLogger(__name__)

CHECK_INTERVAL = getattr(settings, 'CHECK_INTERVAL', 15)


class Command(BaseCommand):
    help = 'Run the WireGuard handshake monitoring scheduler'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting WireGuard handshake monitor...'))
        self.stdout.write(f'Check interval: {CHECK_INTERVAL} seconds')
        self.stdout.write(f'Handshake TTL: {getattr(settings, "HANDSHAKE_TTL", 60)} seconds')
        self.stdout.write(f'WireGuard interface: {getattr(settings, "WG_INTERFACE", "wg0")}')
        
        scheduler = BackgroundScheduler()
        
        scheduler.add_job(
            check_handshakes,
            trigger=IntervalTrigger(seconds=CHECK_INTERVAL),
            id='check_handshakes',
            name='Check WireGuard handshakes',
            replace_existing=True,
            max_instances=1,
        )
        
        scheduler.start()
        self.stdout.write(self.style.SUCCESS('Scheduler started'))
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stdout.write('Shutting down scheduler...')
            scheduler.shutdown()
            self.stdout.write(self.style.SUCCESS('Scheduler stopped'))