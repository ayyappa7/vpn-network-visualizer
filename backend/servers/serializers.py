from rest_framework import serializers
from .models import Server, HandshakeResult


class ServerSerializer(serializers.ModelSerializer):
    primary_ip = serializers.CharField(read_only=True)
    is_reachable = serializers.SerializerMethodField()
    last_handshake = serializers.SerializerMethodField()
    rx_bytes = serializers.SerializerMethodField()
    tx_bytes = serializers.SerializerMethodField()

    def get_is_reachable(self, obj):
        return bool(getattr(obj, 'is_reachable', False))

    def get_last_handshake(self, obj):
        val = getattr(obj, 'last_handshake', None)
        return val.isoformat() if val else None

    def get_rx_bytes(self, obj):
        return getattr(obj, 'rx_bytes', 0) or 0

    def get_tx_bytes(self, obj):
        return getattr(obj, 'tx_bytes', 0) or 0

    class Meta:
        model = Server
        fields = [
            'id', 'name', 'public_key', 'endpoint', 'allowed_ips',
            'persistent_keepalive', 'primary_ip', 'is_active',
            'is_reachable', 'last_handshake', 'rx_bytes', 'tx_bytes',
            'first_seen', 'updated_at',
        ]


class HandshakeResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = HandshakeResult
        fields = [
            'id', 'server', 'last_handshake',
            'rx_bytes', 'tx_bytes', 'is_reachable', 'captured_at'
        ]