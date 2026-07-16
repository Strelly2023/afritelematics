"""WebSocket subscription runtime for integrations."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class WebSocketSubscription:
    channel_id: str
    provider_id: str
    product_code: str
    status: str


@dataclass(slots=True)
class WebSocketSubscriptionRuntime:
    subscriptions: list[WebSocketSubscription] = field(default_factory=list)

    def register(self, subscription: WebSocketSubscription) -> WebSocketSubscription:
        self.subscriptions.append(subscription)
        return subscription

