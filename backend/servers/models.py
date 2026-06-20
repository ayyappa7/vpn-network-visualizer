from django.db import models


class Server(models.Model):
    name = models.CharField(max_length=100, blank=True)
    public_key = models.CharField(max_length=100, unique=True)
    endpoint = models.CharField(max_length=100, blank=True)
    allowed_ips = models.TextField(blank=True)
    persistent_keepalive = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        ips = self.allowed_ips.split(',')[0] if self.allowed_ips else self.public_key[:16]
        return f"{self.name or ips}"

    @property
    def primary_ip(self):
        if self.allowed_ips:
            for cidr in self.allowed_ips.split(','):
                ip = cidr.strip().split('/')[0]
                return ip
        return None

    @property
    def is_reachable(self):
        latest = self.handshakes.first()
        return latest.is_reachable if latest else False


class HandshakeResult(models.Model):
    server = models.ForeignKey(Server, related_name='handshakes', on_delete=models.CASCADE)
    last_handshake = models.DateTimeField(null=True, blank=True)
    rx_bytes = models.BigIntegerField(default=0)
    tx_bytes = models.BigIntegerField(default=0)
    is_reachable = models.BooleanField(default=False)
    captured_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-captured_at']
        indexes = [
            models.Index(fields=['captured_at']),
            models.Index(fields=['server']),
        ]

    def __str__(self):
        status = "✓" if self.is_reachable else "✗"
        return f"{self.server.name} {status}"