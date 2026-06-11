from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from afritech.models import EventRecord
from afritech.proof.contract_receipt_index import (
    ContractReceiptIndexError,
    guard_declared_receipt_matches_timestamp,
    guard_receipt_effective_at,
    resolve_driver_api_receipt_by_hash,
)


# ------------------------------------------------------------------------------------
# DRIVER LIFECYCLE EVENTS
# ------------------------------------------------------------------------------------

DRIVER_LIFECYCLE_EVENT_TYPES = frozenset(
    {
        "DriverAvailabilityChanged",
        "RideAccepted",
        "RideRejected",
        "DriverArrived",
        "RideArrived",
        "TripStarted",
        "RideStarted",
        "TripCompleted",
        "RideCompleted",
    }
)


# ------------------------------------------------------------------------------------
# ERRORS
# ------------------------------------------------------------------------------------

class ContractBindingReplayError(RuntimeError):
    """Raised when replay cannot bind an event to its governing contract receipt."""


# ------------------------------------------------------------------------------------
# REPLAY ENTRY MODEL
# ------------------------------------------------------------------------------------

@dataclass(frozen=True)
class ContractBindingReplayEntry:
    event_id: str
    event_type: str
    subject_id: str
    created_at: str
    contract: str
    version: str
    snapshot_hash: str
    contract_receipt_hash: str
    event_hash: str
    replay_verified: bool
    receipt_resolution: str
    receipt_id: str
    receipt_effective_from: str
    receipt_effective_to: str | None

    def canonical_dict(self) -> Dict[str, Any]:
        """Return canonical representation for deterministic comparisons."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "subject_id": self.subject_id,
            "created_at": self.created_at,
            "contract": self.contract,
            "version": self.version,
            "snapshot_hash": self.snapshot_hash,
            "contract_receipt_hash": self.contract_receipt_hash,
            "event_hash": self.event_hash,
            "replay_verified": self.replay_verified,
            "receipt_resolution": self.receipt_resolution,
            "receipt_id": self.receipt_id,
            "receipt_effective_from": self.receipt_effective_from,
            "receipt_effective_to": self.receipt_effective_to,
        }


# ------------------------------------------------------------------------------------
# VALIDATION CORE
# ------------------------------------------------------------------------------------

def validate_driver_event_contract_binding(
    event: EventRecord,
) -> ContractBindingReplayEntry:
    """Validate and bind a driver lifecycle event to a contract receipt."""

    # --------------------------------------------------------------------------
    # EVENT TYPE VALIDATION
    # --------------------------------------------------------------------------

    if event.event_type not in DRIVER_LIFECYCLE_EVENT_TYPES:
        raise ContractBindingReplayError(
            f"unsupported driver lifecycle event: {event.event_type}"
        )

    if not isinstance(event.payload, dict):
        raise ContractBindingReplayError("event payload must be a dictionary")

    binding = event.payload.get("contract_binding")
    if not isinstance(binding, dict):
        raise ContractBindingReplayError("event missing contract_binding")

    # --------------------------------------------------------------------------
    # RESOLVE RECEIPT FROM INDEX
    # --------------------------------------------------------------------------

    declared_receipt_hash = binding.get("contract_receipt_hash")

    try:
        receipt = resolve_driver_api_receipt_by_hash(
            str(declared_receipt_hash)
        )

        guard_receipt_effective_at(receipt, event.created_at)
        guard_declared_receipt_matches_timestamp(
            receipt,
            event.created_at,
        )

    except ContractReceiptIndexError as exc:
        raise ContractBindingReplayError(
            "event contract receipt cannot resolve from index"
        ) from exc

    # --------------------------------------------------------------------------
    # VERIFY CONTRACT BINDING MATCHES RECEIPT
    # --------------------------------------------------------------------------

    expected: Dict[str, str] = {
        "contract": receipt.contract,
        "version": receipt.version,
        "snapshot_hash": receipt.snapshot_hash,
        "contract_receipt_hash": receipt.receipt_hash,
        "event_hash": receipt.event_hash,
    }

    actual: Dict[str, Any] = {
        key: binding.get(key) for key in expected
    }

    if actual != expected:
        raise ContractBindingReplayError(
            "event contract binding does not match active receipt"
        )

    # --------------------------------------------------------------------------
    # BUILD REPLAY ENTRY
    # --------------------------------------------------------------------------

    return ContractBindingReplayEntry(
        event_id=str(event.event_id),
        event_type=event.event_type,
        subject_id=event.subject_id,
        created_at=event.created_at.isoformat(),
        contract=receipt.contract,
        version=receipt.version,
        snapshot_hash=receipt.snapshot_hash,
        contract_receipt_hash=receipt.receipt_hash,
        event_hash=receipt.event_hash,
        replay_verified=True,
        receipt_resolution="timestamp_aligned_indexed_receipt",
        receipt_id=receipt.receipt_id,
        receipt_effective_from=receipt.effective_from_iso,
        receipt_effective_to=receipt.effective_to_iso,
    )


# ------------------------------------------------------------------------------------
# BATCH REPLAY
# ------------------------------------------------------------------------------------

def replay_driver_event_contract_bindings(
    events: Iterable[EventRecord],
) -> List[ContractBindingReplayEntry]:
    """Replay a sequence of events and resolve their contract bindings."""
    return [
        validate_driver_event_contract_binding(event)
        for event in events
    ]


def replay_all_driver_event_contract_bindings(
) -> List[ContractBindingReplayEntry]:
    """Replay all driver lifecycle events in chronological order."""
    events = EventRecord.objects.filter(
        event_type__in=sorted(DRIVER_LIFECYCLE_EVENT_TYPES)
    ).order_by("created_at", "event_id")

    return replay_driver_event_contract_bindings(events)
