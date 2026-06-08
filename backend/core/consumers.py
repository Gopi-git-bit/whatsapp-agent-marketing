from __future__ import annotations

import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ItemProgressConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for reporting progress on Item processing.

    Clients should connect to `/ws/items/<id>/` to receive progress updates for
    a particular item.  The Celery task will broadcast messages to the
    corresponding group (`item_<id>`), which will be forwarded to the
    connected WebSocket client as JSON.
    """

    async def connect(self) -> None:
        # Extract the item id from the URL route kwargs (set in routing.py)
        self.item_id = self.scope['url_route']['kwargs']['item_id']
        self.group_name = f'item_{self.item_id}'
        # Add the connection to the group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        # Remove the connection from the group on disconnect
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def progress_update(self, event: dict) -> None:
        """
        Handler for progress updates sent by Celery tasks.

        The event dict will contain a `message` key with the JSON serializable
        payload.  This handler simply forwards the message to the WebSocket
        client.
        """
        message = event.get('message', {})
        await self.send(text_data=json.dumps(message))