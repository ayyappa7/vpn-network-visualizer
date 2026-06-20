import json
from channels.generic.websocket import AsyncWebsocketConsumer


class GraphConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("graph_updates", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("graph_updates", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

    async def handshake_update(self, event):
        await self.send(text_data=json.dumps(event['data']))