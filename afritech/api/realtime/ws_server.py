from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from copy import deepcopy
from typing import Any, Protocol


class WebSocketClient(Protocol):
    async def send_json(self, message: Mapping[str, Any]) -> None:
        """Send JSON to a subscribed realtime client."""


class WebSocketHub:
    """Observation-only channel hub for projected ride state."""

    def __init__(self) -> None:
        self.channels: dict[str, list[WebSocketClient]] = defaultdict(list)
        self.sequence_by_ride: dict[str, int] = {}

    def subscribe(self, ride_id: str, client: WebSocketClient) -> None:
        channel = self.channel_for(ride_id)
        if client not in self.channels[channel]:
            self.channels[channel].append(client)

    def unsubscribe(self, ride_id: str, client: WebSocketClient) -> None:
        channel = self.channel_for(ride_id)
        if client in self.channels.get(channel, []):
            self.channels[channel].remove(client)

    async def publish_state_update(
        self,
        ride_id: str,
        data: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Publish observation-only state projection updates."""

        sequence = self.sequence_by_ride.get(ride_id, 0) + 1
        self.sequence_by_ride[ride_id] = sequence
        message = {
            "type": "STATE_UPDATE",
            "ride_id": ride_id,
            "data": deepcopy(dict(data)),
            "sequence": sequence,
            "authority": "projection_only",
        }

        for client in tuple(self.channels.get(self.channel_for(ride_id), ())):
            await client.send_json(message)

        return message

    def channel_for(self, ride_id: str) -> str:
        if not ride_id:
            raise ValueError("ride_id must be non-empty")
        return f"ride_{ride_id}"
