"""AfriRide event ledger validation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from afriride_system.backend.event_signatures import EventSignatureValidator


class EventLedgerValidationError(RuntimeError):
    """Raised when a declared event ledger is not internally admissible."""


RIDE_SEQUENCE = (
    "RIDE_REQUEST_CREATED",
    "DRIVER_ASSIGNED",
    "RIDE_ACCEPTED",
    "RIDE_STARTED",
    "RIDE_COMPLETED",
    "RECEIPT_GENERATED",
)


@dataclass(frozen=True)
class EventLedgerReport:
    event_count: int
    ride_count: int
    completed_ride_count: int
    total_distance_km: float
    total_duration_min: int
    total_fare: float
    declared_chain_terminal_hash: str
    hash_mode: str
    signature_mode: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "event_count": self.event_count,
            "ride_count": self.ride_count,
            "completed_ride_count": self.completed_ride_count,
            "total_distance_km": self.total_distance_km,
            "total_duration_min": self.total_duration_min,
            "total_fare": self.total_fare,
            "declared_chain_terminal_hash": self.declared_chain_terminal_hash,
            "hash_mode": self.hash_mode,
            "signature_mode": self.signature_mode,
            "write_enabled": False,
            "authority": "evidence_validation_only",
        }


class EventLedgerHasher:
    """Create canonical SHA-256 event hash chains."""

    SIGNATURE_FIELDS = frozenset(
        {
            "signer_id",
            "signature",
            "public_key_id",
            "device_id",
            "terms_version",
        }
    )

    @staticmethod
    def compute_event_hash(
        event_without_hash: dict[str, Any],
        previous_hash: str | None,
    ) -> str:
        payload = {
            key: value
            for key, value in event_without_hash.items()
            if key != "hash" and key not in EventLedgerHasher.SIGNATURE_FIELDS
        }
        payload["hash_prev"] = previous_hash
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        previous = previous_hash or ""
        return hashlib.sha256(f"{encoded}{previous}".encode("utf-8")).hexdigest()

    def materialize_sha256_chain(
        self,
        events: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        materialized: list[dict[str, Any]] = []
        previous_hash: str | None = None

        for event in events:
            next_event = {
                key: value
                for key, value in event.items()
                if key not in {"hash", "hash_prev"}
            }
            next_event["hash_prev"] = previous_hash
            next_event["hash"] = self.compute_event_hash(next_event, previous_hash)
            materialized.append(next_event)
            previous_hash = next_event["hash"]

        return materialized


class EventLedgerValidator:
    """
    Validate declared event-ledger consistency.

    The default mode checks declared token linkage. Set
    require_cryptographic_hashes=True to recompute and enforce SHA-256 hashes.
    """

    def __init__(
        self,
        *,
        require_cryptographic_hashes: bool = False,
        hasher: EventLedgerHasher | None = None,
        signature_validator: EventSignatureValidator | None = None,
    ) -> None:
        self.require_cryptographic_hashes = require_cryptographic_hashes
        self.hasher = hasher or EventLedgerHasher()
        self.signature_validator = signature_validator
        if self.signature_validator is not None and not require_cryptographic_hashes:
            raise EventLedgerValidationError(
                "signature validation requires cryptographic hash validation"
            )

    def validate(self, events: list[dict[str, Any]]) -> EventLedgerReport:
        if not events:
            raise EventLedgerValidationError("event ledger is empty")

        self._validate_unique_ids(events)
        self._validate_hash_chain(events)
        self._validate_signatures(events)
        self._validate_time_order(events)

        online_drivers: set[str] = set()
        rides: dict[str, list[dict[str, Any]]] = {}
        completed: list[dict[str, Any]] = []
        receipts: list[dict[str, Any]] = []

        for event in events:
            event_type = self._require_string(event, "type")
            if event_type == "DRIVER_ONLINE":
                online_drivers.add(self._require_string(event, "driver_id"))
                continue

            ride_id = self._require_string(event, "ride_id")
            rides.setdefault(ride_id, []).append(event)

            if event_type == "DRIVER_ASSIGNED":
                driver_id = self._require_string(event, "driver_id")
                if driver_id not in online_drivers:
                    raise EventLedgerValidationError(
                        f"driver assigned before online: {driver_id}"
                    )
            if event_type == "RIDE_COMPLETED":
                completed.append(event)
            if event_type == "RECEIPT_GENERATED":
                receipts.append(event)

        for ride_id, ride_events in rides.items():
            self._validate_ride_sequence(ride_id, ride_events)

        if len(completed) != len(receipts):
            raise EventLedgerValidationError("completed ride count does not match receipts")

        return EventLedgerReport(
            event_count=len(events),
            ride_count=len(rides),
            completed_ride_count=len(completed),
            total_distance_km=sum(float(event["distance_km"]) for event in completed),
            total_duration_min=sum(int(event["duration_min"]) for event in completed),
            total_fare=round(sum(float(event["fare"]) for event in receipts), 2),
            declared_chain_terminal_hash=self._require_string(events[-1], "hash"),
            hash_mode=(
                "sha256_canonical_chain"
                if self.require_cryptographic_hashes
                else "declared_token_chain"
            ),
            signature_mode=(
                "rsa_pss_sha256"
                if self.signature_validator is not None
                else "unsigned"
            ),
        )

    def _validate_unique_ids(self, events: list[dict[str, Any]]) -> None:
        event_ids = [self._require_string(event, "event_id") for event in events]
        if len(event_ids) != len(set(event_ids)):
            raise EventLedgerValidationError("duplicate event_id")

    def _validate_hash_chain(self, events: list[dict[str, Any]]) -> None:
        previous_hash: str | None = None
        for event in events:
            if event.get("hash_prev") != previous_hash:
                raise EventLedgerValidationError(
                    f"declared hash chain break at {event.get('event_id')}"
                )
            if self.require_cryptographic_hashes:
                expected = self.hasher.compute_event_hash(event, previous_hash)
                if event.get("hash") != expected:
                    raise EventLedgerValidationError(
                        f"cryptographic hash mismatch at {event.get('event_id')}"
                    )
            previous_hash = self._require_string(event, "hash")

    def _validate_signatures(self, events: list[dict[str, Any]]) -> None:
        if self.signature_validator is None:
            return
        for event in events:
            self.signature_validator.validate_event(event)

    def _validate_time_order(self, events: list[dict[str, Any]]) -> None:
        previous: datetime | None = None
        for event in events:
            current = datetime.fromisoformat(
                self._require_string(event, "timestamp").replace("Z", "+00:00")
            )
            if previous is not None and current < previous:
                raise EventLedgerValidationError(
                    f"timestamp order break at {event.get('event_id')}"
                )
            previous = current

    def _validate_ride_sequence(
        self,
        ride_id: str,
        events: list[dict[str, Any]],
    ) -> None:
        sequence = tuple(event["type"] for event in events)
        if sequence != RIDE_SEQUENCE:
            raise EventLedgerValidationError(
                f"invalid lifecycle sequence for {ride_id}: {sequence}"
            )

    def _require_string(self, event: dict[str, Any], key: str) -> str:
        value = event.get(key)
        if not isinstance(value, str) or not value.strip():
            raise EventLedgerValidationError(f"missing {key}")
        return value
