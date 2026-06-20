from django.contrib import admin
from .models import Server, HandshakeResult


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ['name', 'public_key_short', 'endpoint', 'allowed_ips', 'is_active', 'first_seen']
    list_filter = ['is_active']
    search_fields = ['name', 'public_key', 'endpoint', 'allowed_ips']
    readonly_fields = ['first_seen', 'updated_at']

    def public_key_short(self, obj):
        return obj.public_key[:20] + '...' if len(obj.public_key) > 20 else obj.public_key
    public_key_short.short_description = 'Public Key'


@admin.register(HandshakeResult)
class HandshakeResultAdmin(admin.ModelAdmin):
    list_display = ['server', 'is_reachable', 'last_handshake', 'rx_bytes', 'tx_bytes', 'captured_at']
    list_filter = ['is_reachable', 'captured_at']
    readonly_fields = ['captured_at']