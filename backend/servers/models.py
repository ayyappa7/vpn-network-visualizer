from django.db import models
from django.utils import timezone


class Server(models.Model):
    name = models.CharField(max_length=100)
    wireguard_ip = models.GenericIPAddressField(protocol='IPv4', unique=True)
    public_key = models.CharField(max_length=100, blank=True, help_text='WireGuard public key for peer identification')
    public_ip = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['wireguard_ip']

    def __str__(self):
        return f"{self.name} ({self.wireguard_ip})"

    @property
    def is_reachable(self):
        latest = self.handshakes.first()
        return latest.is_reachable if latest else False


class HandshakeResult(models.Model):
    server = models.ForeignKey(Server, related_name='handshakes', on_delete=models.CASCADE)
    peer_public_key = models.CharField(max_length=100)
    last_handshake = models.DateTimeField(null=True, blank=True)
    rx_bytes = models.BigIntegerField(default=0)
    tx_bytes = models.BigIntegerField(default=0)
    is_reachable = models.BooleanField(default=False)
    captured_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-captured_at']
        indexes = [
            models.Index(fields=['captured_at']),
            models.Index(fields=['server', 'peer_public_key']),
        ]

    def __str__(self):
        status = "✓" if self.is_reachable else "✗"
        return f"{self.server.name} -> {self.peer_public_key[:8]}... {status}"