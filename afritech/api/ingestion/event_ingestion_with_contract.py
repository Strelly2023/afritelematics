from __future__ import annotations

from typing import Any

from afritech.api.contracts.rules import EventContractRules
from afritech.api.contracts.validator import EventContractValidator
from afritech.api.ingestion.event_ingestion import MobileEventAuthenticator


class EventIngestionPipeline:
    """Contract-only ingress pipeline for schema and rule validation."""

    def __init__(self, secret: str) -> None:
        self.validator = EventContractValidator()
        self.rules = EventContractRules()
        self.auth = MobileEventAuthenticator()
        self.secret = secret

    def ingest(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.validator.validate_batch(payload)

        accepted = []
        rejected = []

        for event in payload["events"]:
            try:
                if not self.auth.verify(event, event["signature"], self.secret):
                    raise ValueError("invalid_signature")

                self.rules.validate(event)
                accepted.append(event)

            except Exception as exc:
                rejected.append(
                    {
                        "event_id": event.get("event_id"),
                        "reason": str(exc),
                    }
                )

        return {
            "accepted": accepted,
            "rejected": rejected,
        }
