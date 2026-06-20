from django.contrib import admin
from .models import Server, HandshakeResult


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ['name', 'wireguard_ip', 'public_key', 'is_active', 'is_reachable', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'wireguard_ip', 'public_key']


@admin.register(HandshakeResult)
class HandshakeResultAdmin(admin.ModelAdmin):
    list_display = ['server', 'is_reachable', 'last_handshake', 'rx_bytes', 'tx_bytes', 'captured_at']
    list_filter = ['is_reachable', 'captured_at']
    search_fields = ['server__name', 'peer_public_key']
    readonly_fields = ['captured_at']