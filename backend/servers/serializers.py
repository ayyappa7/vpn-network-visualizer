from rest_framework import serializers
from .models import Server, HandshakeResult


class ServerSerializer(serializers.ModelSerializer):
    is_reachable = serializers.BooleanField(read_only=True)
    last_handshake = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = Server
        fields = [
            'id', 'name', 'wireguard_ip', 'public_key', 'public_ip',
            'description', 'is_active', 'is_reachable', 'last_handshake',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class HandshakeResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = HandshakeResult
        fields = [
            'id', 'server', 'peer_public_key', 'last_handshake',
            'rx_bytes', 'tx_bytes', 'is_reachable', 'captured_at'
        ]
        read_only_fields = ['captured_at']


class ServerListSerializer(serializers.ModelSerializer):
    is_reachable = serializers.BooleanField(read_only=True)
    last_handshake = serializers.DateTimeField(read_only=True)
    rx_bytes = serializers.IntegerField(read_only=True)
    tx_bytes = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Server
        fields = [
            'id', 'name', 'wireguard_ip', 'public_key', 'public_ip',
            'description', 'is_active', 'is_reachable', 'last_handshake',
            'rx_bytes', 'tx_bytes', 'created_at'
        ]