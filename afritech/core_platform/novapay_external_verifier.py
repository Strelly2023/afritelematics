"""Standalone NovaPay audit package verifier.

This module implements the public NovaPay audit-package protocol without
importing the NovaPay runtime engine. It is intended for external auditors and
offline verification tools that receive an ``audit_package.json`` artifact.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping

from afritech.core_platform.canonical import hash_obj
from afritech.core_platform.hash_domains import HASH_DOMAINS
from afritech.core_platform.signing import verify_packet_signature


GENESIS_HASH = "0" * 64
AUDIT_PACKAGE_SCHEMA = "novapay.audit_package.v1"
CANONICAL_FORMAT = "canonical.v1"
HASH_DOMAIN_VERSION = 1
HASH_ALGORITHM = "sha256"
TRANSFER_STATE_MACHINE = {
    None: ("requested",),
    "requested": ("admission.approved", "admission.rejected"),
    "admission.approved": ("executed", "cancelled"),
    "executed": ("settled", "execution.failed"),
    "settled": ("receipt.generated",),
    "receipt.generated": (),
    "admission.rejected": (),
    "cancelled": (),
    "execution.failed": (),
}
MANDATORY_PREVIOUS_STATES = {
    "admission.approved": "requested",
    "executed": "admission.approved",
    "settled": "executed",
    "receipt.generated": "settled",
}
EVENT_STATE_MAP = {
    "transfer.requested.v1": "requested",
    "transfer.admission.approved.v1": "admission.approved",
    "transfer.admission.rejected.v1": "admission.rejected",
    "transfer.cancelled.v1": "cancelled",
    "transfer.executed.v1": "executed",
    "transfer.execution.failed.v1": "execution.failed",
    "transfer.settled.v1": "settled",
    "receipt.generated.v1": "receipt.generated",
}
EVENT_SCHEMA_REGISTRY = {event_type: frozenset({1}) for event_type in EVENT_STATE_MAP}
STATE_CHANGING_EVENTS = frozenset(EVENT_STATE_MAP)
SOURCE_BODY_KEYS = (
    "schema",
    "canonical_format",
    "hash_domain_version",
    "hash_algorithm",
    "transfer",
    "admission",
    "receipt",
    "ledger",
    "journal_entry",
    "settlement",
    "events",
    "policy",
    "snapshot",
    "transfer_merkle_root",
    "transfer_root_commitment",
    "merkle_proofs",
    "global_ledger_root",
    "ledger_checkpoint",
    "reconciliation",
    "verification_instructions",
)


class NovaPayExternalVerificationError(ValueError):
    """Raised when an audit package violates the public verification protocol."""


@dataclass(frozen=True)
class ExternalTransferEvent:
    event_id: str
    transfer_id: str
    event_type: str
    occurred_at: str
    payload: dict[str, Any]
    decision_trace: dict[str, Any]
    sequence: int = 0
    schema_version: int = 1
    aggregate_version: int = 0
    previous_event_hash: str = GENESIS_HASH
    event_hash: str = ""

    def canonical(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "transfer_id": self.transfer_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "sequence": self.sequence,
            "schema_version": self.schema_version,
            "aggregate_version": self.aggregate_version,
            "previous_event_hash": self.previous_event_hash,
            "event_hash": self.event_hash,
            "payload": dict(self.payload),
            "decision_trace": dict(self.decision_trace),
        }

    def commitment_payload(self) -> dict[str, Any]:
        payload = self.canonical()
        payload.pop("event_hash", None)
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ExternalTransferEvent":
        return cls(
            event_id=str(payload["event_id"]),
            transfer_id=str(payload["transfer_id"]),
            event_type=str(payload["event_type"]),
            occurred_at=str(payload["occurred_at"]),
            payload=dict(payload.get("payload") or {}),
            decision_trace=dict(payload.get("decision_trace") or {}),
            sequence=int(payload.get("sequence") or 0),
            schema_version=int(payload.get("schema_version") or 1),
            aggregate_version=int(payload.get("aggregate_version") or 0),
            previous_event_hash=str(payload.get("previous_event_hash") or GENESIS_HASH),
            event_hash=str(payload.get("event_hash") or ""),
        )


def verify_audit_package(package: Mapping[str, Any]) -> dict[str, Any]:
    """Verify a NovaPay audit package without runtime state.

    The result is diagnostic by design: every boolean is independently
    recomputed from source package data, and ``valid`` is true only when all
    protocol checks pass.
    """

    protocol_valid = _protocol_valid(package)
    source_body = {key: package.get(key) for key in SOURCE_BODY_KEYS}
    root_hash = hash_obj(source_body, domain=HASH_DOMAINS["AUDIT_PACKAGE"])
    signature_valid = _signature_valid(package, root_hash)
    try:
        recomputed_ledger_hash = _ledger_hash(package.get("ledger") or [])
        ledger_hash_valid = package.get("ledger_hash") == recomputed_ledger_hash
    except Exception:
        recomputed_ledger_hash = ""
        ledger_hash_valid = False
    event_chain_valid = _event_chain_valid(package.get("events") or [])
    try:
        snapshot_root_valid, snapshot_ledger_valid = _snapshot_valid(package)
    except Exception:
        snapshot_root_valid = False
        snapshot_ledger_valid = False
    try:
        transfer_merkle_valid = _transfer_merkle_valid(package)
    except Exception:
        transfer_merkle_valid = False
    try:
        ledger_checkpoint_valid = _ledger_checkpoint_valid(package)
    except Exception:
        ledger_checkpoint_valid = False
    try:
        reconciliation_valid = _reconciliation_valid(package)
    except Exception:
        reconciliation_valid = False

    return {
        "valid": bool(
            root_hash == package.get("root_hash")
            and protocol_valid
            and signature_valid
            and ledger_hash_valid
            and snapshot_root_valid
            and snapshot_ledger_valid
            and event_chain_valid
            and transfer_merkle_valid
            and ledger_checkpoint_valid
            and reconciliation_valid
        ),
        "root_hash": root_hash,
        "protocol_valid": bool(protocol_valid),
        "signature_valid": bool(signature_valid),
        "ledger_hash_valid": bool(ledger_hash_valid),
        "snapshot_root_valid": bool(snapshot_root_valid),
        "snapshot_ledger_valid": bool(snapshot_ledger_valid),
        "event_chain_valid": bool(event_chain_valid),
        "transfer_merkle_valid": bool(transfer_merkle_valid),
        "ledger_checkpoint_valid": bool(ledger_checkpoint_valid),
        "reconciliation_valid": bool(reconciliation_valid),
        "ledger_hash": recomputed_ledger_hash,
    }


def _protocol_valid(package: Mapping[str, Any]) -> bool:
    return (
        package.get("schema") == AUDIT_PACKAGE_SCHEMA
        and package.get("canonical_format") == CANONICAL_FORMAT
        and package.get("hash_domain_version") == HASH_DOMAIN_VERSION
        and package.get("hash_algorithm") == HASH_ALGORITHM
    )


def _signature_valid(package: Mapping[str, Any], root_hash: str) -> bool:
    transfer_id = (package.get("transfer") or {}).get("transfer_id")
    try:
        return verify_packet_signature(
            {"root_hash": root_hash, "transfer_id": transfer_id},
            package.get("signature") or {},
        )
    except Exception:
        return False


def _ledger_hash(ledger_entries: Any) -> str:
    if not isinstance(ledger_entries, list):
        raise NovaPayExternalVerificationError("ledger_must_be_list")
    normalized = [_normalize_ledger_entry(entry) for entry in ledger_entries]
    return hash_obj(normalized, domain=HASH_DOMAINS["LEDGER_ENTRY"])


def _normalize_ledger_entry(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "ledger_entry_id": str(payload["ledger_entry_id"]),
        "transfer_id": str(payload["transfer_id"]),
        "account_id": str(payload["account_id"]),
        "entry_type": str(payload["entry_type"]),
        "amount": str(_decimal(payload["amount"])),
        "currency": str(payload["currency"]),
        "balance_after": str(_decimal(payload["balance_after"])),
        "created_at": str(payload["created_at"]),
    }


def _event_chain_valid(raw_events: Any) -> bool:
    try:
        if not isinstance(raw_events, list):
            raise NovaPayExternalVerificationError("events_must_be_list")
        events = tuple(ExternalTransferEvent.from_dict(event) for event in raw_events)
        _validate_event_sequence(events)
        return True
    except Exception:
        return False


def _validate_event_sequence(events: tuple[ExternalTransferEvent, ...]) -> None:
    seen_event_ids: set[str] = set()
    seen_event_types: set[str] = set()
    previous_timestamp: datetime | None = None
    previous_hash = GENESIS_HASH
    previous_aggregate_version = 0
    current_state: str | None = None

    if not events:
        raise NovaPayExternalVerificationError("event_sequence_empty")

    for index, event in enumerate(events, start=1):
        state = EVENT_STATE_MAP.get(event.event_type)
        if state is None:
            raise NovaPayExternalVerificationError(f"event_type_not_registered:{event.event_type}")
        allowed_schema_versions = EVENT_SCHEMA_REGISTRY.get(event.event_type)
        if allowed_schema_versions is None or event.schema_version not in allowed_schema_versions:
            raise NovaPayExternalVerificationError(
                f"schema_version_invalid:{event.event_type}:{event.schema_version}"
            )
        if event.event_id in seen_event_ids:
            raise NovaPayExternalVerificationError(f"event_duplicate_id:{event.event_id}")
        seen_event_ids.add(event.event_id)

        if event.event_type in seen_event_types:
            raise NovaPayExternalVerificationError(f"event_duplicate_type:{event.event_type}")
        seen_event_types.add(event.event_type)

        allowed_states = TRANSFER_STATE_MACHINE.get(current_state, ())
        if state not in allowed_states:
            raise NovaPayExternalVerificationError(f"invalid_transition:{current_state}->{state}")
        required_previous = MANDATORY_PREVIOUS_STATES.get(state)
        if required_previous is not None and current_state != required_previous:
            raise NovaPayExternalVerificationError(
                f"missing_required_transition:{required_previous}->{state}"
            )
        if event.sequence != index:
            raise NovaPayExternalVerificationError(f"event_sequence_number_invalid:{event.event_id}")
        expected_aggregate_version = (
            previous_aggregate_version + 1
            if event.event_type in STATE_CHANGING_EVENTS
            else previous_aggregate_version
        )
        if event.aggregate_version != expected_aggregate_version:
            raise NovaPayExternalVerificationError(
                f"event_aggregate_version_invalid:{event.event_id}"
            )
        if event.transfer_id != events[0].transfer_id:
            raise NovaPayExternalVerificationError("event_transfer_id_mismatch")

        event_hash = hash_obj(event.commitment_payload(), domain=HASH_DOMAINS["TRANSFER_EVENT"])
        if event.event_hash != event_hash:
            raise NovaPayExternalVerificationError(f"event_hash_invalid:{event.event_id}")
        if event.previous_event_hash != previous_hash:
            raise NovaPayExternalVerificationError(f"event_hash_chain_broken:{event.event_id}")

        occurred_at = _parse_timestamp(event.occurred_at)
        if previous_timestamp is not None and occurred_at < previous_timestamp:
            raise NovaPayExternalVerificationError(f"event_timestamp_regressed:{event.event_id}")
        previous_timestamp = occurred_at
        previous_hash = event.event_hash
        previous_aggregate_version = event.aggregate_version
        current_state = state


def _snapshot_valid(package: Mapping[str, Any]) -> tuple[bool, bool]:
    snapshot = package.get("snapshot") or {}
    if not snapshot:
        return True, True
    if not isinstance(snapshot, Mapping):
        return False, False
    snapshot_root_hash = hash_obj(
        {
            "state": snapshot.get("state"),
            "ledger_hash": snapshot.get("ledger_hash"),
            "event_hash": snapshot.get("event_hash"),
        },
        domain=HASH_DOMAINS["SNAPSHOT"],
    )
    snapshot_root_valid = snapshot.get("snapshot_root_hash") == snapshot_root_hash
    snapshot_ledger_valid = snapshot.get("ledger_hash") == package.get("ledger_hash")
    return bool(snapshot_root_valid), bool(snapshot_ledger_valid)


def _merkle_parent(left: str, right: str) -> str:
    return hash_obj({"left": left, "right": right}, domain=HASH_DOMAINS["MERKLE_ROOT"])


def _merkle_root_from_hashes(hashes: list[str]) -> str:
    if not hashes:
        return hash_obj({"leaves": []}, domain=HASH_DOMAINS["MERKLE_ROOT"])
    level = list(hashes)
    while len(level) > 1:
        next_level: list[str] = []
        for index in range(0, len(level), 2):
            left = level[index]
            right = level[index + 1] if index + 1 < len(level) else left
            next_level.append(_merkle_parent(left, right))
        level = next_level
    return level[0]


def _verify_merkle_proof(leaf_hash: str, proof: Mapping[str, Any], root_hash: str) -> bool:
    current = leaf_hash
    for step in proof.get("path") or []:
        sibling = str(step.get("hash"))
        if step.get("position") == "left":
            current = _merkle_parent(sibling, current)
        elif step.get("position") == "right":
            current = _merkle_parent(current, sibling)
        else:
            return False
    return current == root_hash


def _transfer_merkle_valid(package: Mapping[str, Any]) -> bool:
    events = [ExternalTransferEvent.from_dict(event) for event in (package.get("events") or [])]
    if not events:
        return False
    leaves = [hash_obj(event.canonical(), domain=HASH_DOMAINS["MERKLE_LEAF"]) for event in events]
    root = _merkle_root_from_hashes(leaves)
    if package.get("transfer_merkle_root") != root:
        return False
    commitment = package.get("transfer_root_commitment") or {}
    if commitment.get("transfer_merkle_root") != root:
        return False
    proofs = package.get("merkle_proofs") or []
    if len(proofs) != len(events):
        return False
    for event, leaf, proof in zip(events, leaves, proofs):
        if proof.get("event_id") != event.event_id:
            return False
        if proof.get("event_type") != event.event_type:
            return False
        if proof.get("sequence") != event.sequence:
            return False
        if proof.get("aggregate_version") != event.aggregate_version:
            return False
        if proof.get("event_hash") != event.event_hash:
            return False
        if proof.get("leaf_hash") != leaf:
            return False
        if not _verify_merkle_proof(leaf, proof, root):
            return False
    return True


def _ledger_checkpoint_valid(package: Mapping[str, Any]) -> bool:
    checkpoint = package.get("ledger_checkpoint") or {}
    if not isinstance(checkpoint, Mapping) or not checkpoint:
        return False
    transfer_roots = checkpoint.get("transfer_roots") or []
    leaf_hashes = [
        hash_obj(root, domain=HASH_DOMAINS["MERKLE_LEAF"])
        for root in sorted(transfer_roots, key=lambda item: str(item.get("transfer_id")))
    ]
    ledger_root = _merkle_root_from_hashes(leaf_hashes)
    accounts = checkpoint.get("accounts") or []
    balances_hash = hash_obj(accounts, domain=HASH_DOMAINS["LEDGER_ENTRY"])
    checkpoint_body = {
        "ledger_root": ledger_root,
        "accounts": accounts,
        "balances_hash": balances_hash,
        "block_height": checkpoint.get("block_height"),
        "previous_snapshot_hash": checkpoint.get("previous_snapshot_hash"),
    }
    return bool(
        package.get("global_ledger_root") == ledger_root
        and checkpoint.get("ledger_root") == ledger_root
        and checkpoint.get("balances_hash") == balances_hash
        and checkpoint.get("snapshot_hash") == hash_obj(
            checkpoint_body,
            domain=HASH_DOMAINS["LEDGER_CHECKPOINT"],
        )
    )


def _reconciliation_valid(package: Mapping[str, Any]) -> bool:
    report = package.get("reconciliation") or {}
    if not isinstance(report, Mapping) or not report:
        return False
    report_body = {
        "total_debit": str(_decimal(report.get("total_debit", "0"))),
        "total_credit": str(_decimal(report.get("total_credit", "0"))),
        "ledger_balanced": bool(report.get("ledger_balanced")),
        "ledger_root": report.get("ledger_root"),
        "total_transfers": report.get("total_transfers"),
    }
    return bool(
        report.get("ledger_balanced") is True
        and report.get("ledger_root") == package.get("global_ledger_root")
        and report.get("report_hash") == hash_obj(
            report_body,
            domain=HASH_DOMAINS["RECONCILIATION_REPORT"],
        )
    )


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _decimal(value: Any) -> Decimal:
    if isinstance(value, bool):
        raise TypeError("non-canonical numeric type: bool")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


__all__ = ["NovaPayExternalVerificationError", "verify_audit_package"]
