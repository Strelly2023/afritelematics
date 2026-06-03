from __future__ import annotations

import hmac
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from fastapi import APIRouter

from afritech.api.contracts.rules import EventContractRules
from afritech.api.contracts.validator import EventContractValidator
from afritech.edge.normalization.reality_events import normalize_reality_events
from afritech.security.integrity_trace import IntegrityTrace


ALLOWED_EVENT_TYPES = frozenset(
    {
        "RIDER_REQUESTED_RIDE",
        "RIDER_CANCELLED_RIDE",
        "DRIVER_ACCEPTED_RIDE",
        "DRIVER_ARRIVED",
        "TRIP_STARTED",
        "TRIP_COMPLETED",
        "DRIVER_LOCATION_UPDATE",
        "PAYMENT_TRIGGERED",
        "PAYMENT_CONFIRMED",
    }
)

REQUIRED_EVENT_FIELDS = frozenset(
    {
        "event_id",
        "event_type",
        "device_id",
        "entity_id",
        "timestamp",
        "logical_clock",
        "payload",
        "signature",
    }
)


class MobileEventAuthenticator:
    """HMAC signer for the canonical mobile event contract."""

    def generate_signature(self, event: Mapping[str, Any], secret: str) -> str:
        payload = IntegrityTrace.canonical_json(self._signed_payload(event))
        return hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            "sha256",
        ).hexdigest()

    def verify(self, event: Mapping[str, Any], signature: str, secret: str) -> bool:
        expected = self.generate_signature(event, secret)
        return hmac.compare_digest(expected, str(signature))

    def _signed_payload(self, event: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "device_id": event["device_id"],
            "entity_id": event["entity_id"],
            "event_id": event["event_id"],
            "event_type": event["event_type"],
            "logical_clock": event["logical_clock"],
            "payload": event["payload"],
            "timestamp": event["timestamp"],
        }


class EventIngestionAPI:
    """Strict mobile-event ingress gate; it never mutates runtime state."""

    def __init__(self, secret: str, *, source_adapter_version: str = "mobile-v1") -> None:
        if not secret:
            raise ValueError("secret must be non-empty")
        self.secret = secret
        self.source_adapter_version = source_adapter_version
        self.auth = MobileEventAuthenticator()
        self.validator = EventContractValidator()
        self.rules = EventContractRules()

    def ingest(
        self,
        events: Sequence[Mapping[str, Any]],
        *,
        received_at_ms: int,
    ) -> dict[str, Any]:
        accepted: list[str] = []
        rejected: list[dict[str, str | None]] = []
        accepted_events: list[dict[str, Any]] = []

        for event in events:
            event_id = _event_id_or_none(event)

            reason = self.validator.event_error(event)
            if reason is not None:
                rejected.append({"event_id": event_id, "reason": reason})
                continue

            canonical_event = deepcopy(dict(event))
            signature = str(canonical_event["signature"])
            if not self.auth.verify(canonical_event, signature, self.secret):
                rejected.append({"event_id": event_id, "reason": "invalid_signature"})
                continue

            try:
                self.rules.validate(canonical_event)
            except ValueError as exc:
                rejected.append({"event_id": event_id, "reason": str(exc)})
                continue

            accepted.append(canonical_event["event_id"])
            accepted_events.append(canonical_event)

        normalized_events = normalize_reality_events(
            tuple(
                _to_reality_observation(event, received_at_ms=received_at_ms)
                for event in accepted_events
            ),
            source_adapter_version=self.source_adapter_version,
        )

        return {
            "accepted": accepted,
            "rejected": rejected,
            "normalized_events": normalized_events,
        }


def build_router(api: EventIngestionAPI) -> APIRouter:
    router = APIRouter()

    @router.post("/v1/events")
    def ingest_events(payload: dict[str, Any]) -> dict[str, Any]:
        events = payload.get("events")
        if not isinstance(events, list):
            return {
                "accepted": [],
                "rejected": [{"event_id": None, "reason": "invalid_request"}],
            }
        received_at_ms = int(payload.get("received_at_ms", 0))
        result = api.ingest(events, received_at_ms=received_at_ms)
        return {
            "accepted": result["accepted"],
            "rejected": result["rejected"],
        }

    return router


def _event_id_or_none(event: Any) -> str | None:
    if isinstance(event, Mapping):
        value = event.get("event_id")
        if isinstance(value, str):
            return value
    return None


def _is_hex_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(character in "0123456789abcdef" for character in value)


def _to_reality_observation(
    event: Mapping[str, Any],
    *,
    received_at_ms: int,
) -> dict[str, Any]:
    payload = dict(event["payload"])
    payload.setdefault("device_id", event["device_id"])
    payload.setdefault("entity_id", event["entity_id"])
    payload.setdefault("logical_clock", event["logical_clock"])

    return {
        "source_id": event["device_id"],
        "event_id": event["event_id"],
        "event_kind": event["event_type"],
        "observed_at_ms": event["timestamp"],
        "received_at_ms": received_at_ms,
        "payload": payload,
    }
