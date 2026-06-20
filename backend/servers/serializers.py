from rest_framework import serializers
from .models import Server, HandshakeResult


class ServerSerializer(serializers.ModelSerializer):
    is_reachable = serializers.SerializerMethodField()
    last_handshake = serializers.SerializerMethodField()

    def get_is_reachable(self, obj):
        return bool(getattr(obj, 'is_reachable', False))

    def get_last_handshake(self, obj):
        return getattr(obj, 'last_handshake', None)

    class Meta:
        model = Server
        fields = [
            'id', 'name', 'wireguard_ip', 'public_key', 'public_ip',
            'description', 'is_active', 'is_reachable', 'last_handshake',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ServerListSerializer(serializers.ModelSerializer):
    is_reachable = serializers.SerializerMethodField()
    last_handshake = serializers.SerializerMethodField()
    rx_bytes = serializers.SerializerMethodField()
    tx_bytes = serializers.SerializerMethodField()

    def get_is_reachable(self, obj):
        return bool(getattr(obj, 'is_reachable', False))

    def get_last_handshake(self, obj):
        return getattr(obj, 'last_handshake', None)

    def get_rx_bytes(self, obj):
        return getattr(obj, 'rx_bytes', 0) or 0

    def get_tx_bytes(self, obj):
        return getattr(obj, 'tx_bytes', 0) or 0

    class Meta:
        model = Server
        fields = [
            'id', 'name', 'wireguard_ip', 'public_key', 'public_ip',
            'description', 'is_active', 'is_reachable', 'last_handshake',
            'rx_bytes', 'tx_bytes', 'created_at'
        ]


class HandshakeResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = HandshakeResult
        fields = [
            'id', 'server', 'peer_public_key', 'last_handshake',
            'rx_bytes', 'tx_bytes', 'is_reachable', 'captured_at'
        ]
        read_only_fields = ['captured_at']