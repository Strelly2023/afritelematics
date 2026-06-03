import json

from channels.generic.websocket import AsyncWebsocketConsumer


class RideConsumer(AsyncWebsocketConsumer):
    """Ride-level realtime projection consumer."""

    async def connect(self):
        self.ride_id = self.scope["url_route"]["kwargs"]["ride_id"]
        self.group_name = f"ride_{self.ride_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def ride_event(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "event_type": event["event_type"],
                    "payload": event["payload"],
                    "authority": "notification_only",
                }
            )
        )


class OperatorMonitorConsumer(AsyncWebsocketConsumer):
    """Operator realtime monitor consumer."""

    async def connect(self):
        self.group_name = "operator_monitor"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def operator_event(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "event_type": event["event_type"],
                    "payload": event["payload"],
                    "authority": "notification_only",
                }
            )
        )
