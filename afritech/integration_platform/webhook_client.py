"""Outbound webhook runtime for integration delivery."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class WebhookDeliveryRecord:
    webhook_id: str
    destination: str
    event_type: str
    attempt: int
    status: str
    response_code: int | None
    duration_ms: float
    correlation_id: str
    timestamp: float


@dataclass(slots=True)
class WebhookDeliveryRuntime:
    deliveries: list[WebhookDeliveryRecord] = field(default_factory=list)

    def record(self, delivery: WebhookDeliveryRecord) -> WebhookDeliveryRecord:
        self.deliveries.append(delivery)
        return delivery

