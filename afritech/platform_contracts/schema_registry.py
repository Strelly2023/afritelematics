"""Runtime NovaRide schema registry, validator, and compatibility engine."""

from __future__ import annotations

from dataclasses import dataclass
import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator
import yaml

from afritech.core_platform.signing import sign_packet, verify_packet_signature


ROOT = Path(__file__).resolve().parents[2]
EVENT_REGISTRY_PATH = ROOT / "docs/registry/NOVARIDE_EVENT_REGISTRY.yaml"
EVENT_SCHEMA_OUTPUT_DIR = ROOT / "docs/architecture/generated"
EVENT_SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"
EVENT_REGISTRY_ID = "NOVARIDE_EVENT_REGISTRY_V1"


class SchemaRegistryError(ValueError):
    """Raised when schema registry admission fails."""


@dataclass(frozen=True)
class SchemaRegistryEntry:
    event_type: str
    domain: str
    owner_service: str
    schema_version: int
    compatibility: str
    status: str
    partition_key_strategy: str
    idempotency_strategy: str
    decision_trace_required: bool

    @property
    def certified(self) -> bool:
        return self.status.strip().lower() == "active"


@dataclass(frozen=True)
class CompatibilityReport:
    backward_compatible: bool
    forward_compatible: bool
    breaking_changes: tuple[str, ...]
    warnings: tuple[str, ...]

    def canonical(self) -> dict[str, Any]:
        return {
            "backward_compatible": self.backward_compatible,
            "forward_compatible": self.forward_compatible,
            "breaking_changes": list(self.breaking_changes),
            "warnings": list(self.warnings),
        }


def _money_schema() -> dict[str, Any]:
    return {"type": "string", "pattern": r"^-?\d+(?:\.\d{1,2})?$"}


def _location_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["lat", "lng"],
        "properties": {
            "lat": {"type": "number"},
            "lng": {"type": "number"},
            "label": {"type": "string"},
        },
        "additionalProperties": False,
    }


def _string_schema(*, min_length: int = 1) -> dict[str, Any]:
    return {"type": "string", "minLength": min_length}


def _integer_schema(*, minimum: int = 0) -> dict[str, Any]:
    return {"type": "integer", "minimum": minimum}


def _number_schema(*, minimum: float | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "number"}
    if minimum is not None:
        schema["minimum"] = minimum
    return schema


def _boolean_schema() -> dict[str, Any]:
    return {"type": "boolean"}


def _array_schema(items: dict[str, Any], *, min_items: int = 0, unique: bool = False) -> dict[str, Any]:
    schema = {"type": "array", "items": items}
    if min_items:
        schema["minItems"] = min_items
    if unique:
        schema["uniqueItems"] = True
    return schema


def _object_schema(
    properties: Mapping[str, Any],
    *,
    required: Iterable[str] = (),
    additional_properties: bool = False,
) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": dict(properties),
        "required": list(required),
        "additionalProperties": additional_properties,
    }


def _decision_trace_schema(*, required: bool) -> dict[str, Any]:
    base = {
        "type": "object",
        "properties": {
            "policy_id": {"type": ["string", "null"]},
            "policy_version": {"type": ["string", "null"]},
            "rule_ids": _array_schema({"type": "string"}, unique=True),
            "approval_id": {"type": ["string", "null"]},
            "flag_evaluations": {"type": "object", "additionalProperties": True},
            "evaluation_result": {"type": ["string", "null"]},
            "reviewer": {"type": ["string", "null"]},
            "reason": {"type": ["string", "null"]},
        },
        "additionalProperties": False,
    }
    if required:
        base["required"] = [
            "policy_id",
            "policy_version",
            "rule_ids",
            "flag_evaluations",
            "evaluation_result",
        ]
    return base


EVENT_PAYLOAD_SCHEMAS: dict[str, dict[str, Any]] = {
    "organization.created.v1": _object_schema(
        {
            "organization_id": _string_schema(),
            "name": _string_schema(),
            "org_type": _string_schema(),
            "status": _string_schema(),
        },
        required=("organization_id", "name", "org_type", "status"),
    ),
    "organization.updated.v1": _object_schema(
        {
            "organization_id": _string_schema(),
            "name": _string_schema(),
            "org_type": _string_schema(),
            "status": _string_schema(),
        },
        required=("organization_id",),
    ),
    "account.created.v1": _object_schema(
        {
            "account_id": _string_schema(),
            "user_id": _string_schema(),
            "organization_id": _string_schema(),
            "role": _string_schema(),
            "status": _string_schema(),
        },
        required=("account_id", "user_id", "organization_id", "role", "status"),
    ),
    "account.role_assigned.v1": _object_schema(
        {
            "account_id": _string_schema(),
            "user_id": _string_schema(),
            "organization_id": _string_schema(),
            "previous_role": _string_schema(),
            "assigned_role": _string_schema(),
        },
        required=("account_id", "user_id", "organization_id", "assigned_role"),
    ),
    "subscription.activated.v1": _object_schema(
        {
            "subscription_id": _string_schema(),
            "organization_id": _string_schema(),
            "plan": _string_schema(),
            "billing_cycle": _string_schema(),
            "status": _string_schema(),
        },
        required=("subscription_id", "organization_id", "plan", "billing_cycle", "status"),
    ),
    "feature_flag.evaluated.v1": _object_schema(
        {
            "flag_key": _string_schema(),
            "organization_id": _string_schema(),
            "enabled": _boolean_schema(),
            "variant": {"type": ["string", "null"]},
            "reason": {"type": ["string", "null"]},
        },
        required=("flag_key", "organization_id", "enabled"),
    ),
    "ride.requested.v1": _object_schema(
        {
            "ride_id": _string_schema(),
            "passenger_id": _string_schema(),
            "organization_id": _string_schema(),
            "pickup_location": _location_schema(),
            "destination_location": _location_schema(),
            "requested_at": {"type": "string"},
            "currency": _string_schema(),
            "fare_estimate": _money_schema(),
            "status": _string_schema(),
        },
        required=(
            "ride_id",
            "passenger_id",
            "organization_id",
            "pickup_location",
            "destination_location",
            "requested_at",
            "currency",
            "fare_estimate",
            "status",
        ),
    ),
    "ride.matched.v1": _object_schema(
        {
            "ride_id": _string_schema(),
            "organization_id": _string_schema(),
            "driver_id": _string_schema(),
            "dispatch_id": _string_schema(),
            "matched_at": {"type": "string"},
            "status": _string_schema(),
        },
        required=("ride_id", "organization_id", "driver_id", "dispatch_id", "matched_at", "status"),
    ),
    "ride.accepted.v1": _object_schema(
        {
            "ride_id": _string_schema(),
            "organization_id": _string_schema(),
            "driver_id": _string_schema(),
            "accepted_at": {"type": "string"},
            "status": _string_schema(),
        },
        required=("ride_id", "organization_id", "driver_id", "accepted_at", "status"),
    ),
    "ride.arriving.v1": _object_schema(
        {
            "ride_id": _string_schema(),
            "organization_id": _string_schema(),
            "driver_id": _string_schema(),
            "eta_seconds": _integer_schema(),
            "status": _string_schema(),
        },
        required=("ride_id", "organization_id", "driver_id", "eta_seconds", "status"),
    ),
    "ride.arrived.v1": _object_schema(
        {
            "ride_id": _string_schema(),
            "organization_id": _string_schema(),
            "driver_id": _string_schema(),
            "arrived_at": {"type": "string"},
            "status": _string_schema(),
        },
        required=("ride_id", "organization_id", "driver_id", "arrived_at", "status"),
    ),
    "trip.started.v1": _object_schema(
        {
            "ride_id": _string_schema(),
            "trip_id": _string_schema(),
            "organization_id": _string_schema(),
            "driver_id": _string_schema(),
            "passenger_id": _string_schema(),
            "started_at": {"type": "string"},
            "pickup_location": _location_schema(),
            "status": _string_schema(),
        },
        required=(
            "ride_id",
            "trip_id",
            "organization_id",
            "driver_id",
            "passenger_id",
            "started_at",
            "pickup_location",
            "status",
        ),
    ),
    "trip.completed.v1": _object_schema(
        {
            "ride_id": _string_schema(),
            "trip_id": _string_schema(),
            "organization_id": _string_schema(),
            "driver_id": _string_schema(),
            "passenger_id": _string_schema(),
            "final_fare": _money_schema(),
            "currency": _string_schema(),
            "distance_meters": _integer_schema(),
            "duration_seconds": _integer_schema(),
            "route_distance_meters": _integer_schema(),
            "route_duration_seconds": _integer_schema(),
            "status": _string_schema(),
        },
        required=(
            "ride_id",
            "trip_id",
            "organization_id",
            "driver_id",
            "passenger_id",
            "final_fare",
            "currency",
            "distance_meters",
            "duration_seconds",
            "route_distance_meters",
            "route_duration_seconds",
            "status",
        ),
    ),
    "trip.cancelled.v1": _object_schema(
        {
            "ride_id": _string_schema(),
            "trip_id": _string_schema(),
            "organization_id": _string_schema(),
            "driver_id": {"type": ["string", "null"]},
            "cancelled_by": _string_schema(),
            "reason": _string_schema(),
            "status": _string_schema(),
        },
        required=("ride_id", "trip_id", "organization_id", "cancelled_by", "reason", "status"),
    ),
    "driver.presence.updated.v1": _object_schema(
        {
            "driver_id": _string_schema(),
            "organization_id": _string_schema(),
            "status": _string_schema(),
            "location": _location_schema(),
            "last_seen": {"type": "string"},
        },
        required=("driver_id", "organization_id", "status", "location", "last_seen"),
    ),
    "dispatch.assignment_created.v1": _object_schema(
        {
            "assignment_id": _string_schema(),
            "ride_id": _string_schema(),
            "organization_id": _string_schema(),
            "driver_id": _string_schema(),
            "dispatch_strategy": _string_schema(),
            "status": _string_schema(),
        },
        required=("assignment_id", "ride_id", "organization_id", "driver_id", "dispatch_strategy", "status"),
    ),
    "dispatch.assignment_released.v1": _object_schema(
        {
            "assignment_id": _string_schema(),
            "ride_id": _string_schema(),
            "organization_id": _string_schema(),
            "driver_id": _string_schema(),
            "reason": _string_schema(),
            "status": _string_schema(),
        },
        required=("assignment_id", "ride_id", "organization_id", "driver_id", "reason", "status"),
    ),
    "payment.authorized.v1": _object_schema(
        {
            "payment_id": _string_schema(),
            "ride_id": _string_schema(),
            "organization_id": _string_schema(),
            "amount": _money_schema(),
            "currency": _string_schema(),
            "provider": _string_schema(),
            "provider_reference": _string_schema(),
            "status": _string_schema(),
        },
        required=(
            "payment_id",
            "ride_id",
            "organization_id",
            "amount",
            "currency",
            "provider",
            "provider_reference",
            "status",
        ),
    ),
    "payment.captured.v1": _object_schema(
        {
            "payment_id": _string_schema(),
            "ride_id": _string_schema(),
            "organization_id": _string_schema(),
            "amount": _money_schema(),
            "currency": _string_schema(),
            "provider": _string_schema(),
            "provider_capture_id": _string_schema(),
            "status": _string_schema(),
        },
        required=(
            "payment_id",
            "ride_id",
            "organization_id",
            "amount",
            "currency",
            "provider",
            "provider_capture_id",
            "status",
        ),
    ),
    "payment.failed.v1": _object_schema(
        {
            "payment_id": _string_schema(),
            "ride_id": _string_schema(),
            "organization_id": _string_schema(),
            "amount": _money_schema(),
            "currency": _string_schema(),
            "provider": _string_schema(),
            "failure_code": _string_schema(),
            "failure_reason": _string_schema(),
            "status": _string_schema(),
        },
        required=(
            "payment_id",
            "ride_id",
            "organization_id",
            "amount",
            "currency",
            "provider",
            "failure_code",
            "failure_reason",
            "status",
        ),
    ),
    "wallet.debited.v1": _object_schema(
        {
            "wallet_id": _string_schema(),
            "user_id": _string_schema(),
            "ride_id": _string_schema(),
            "organization_id": _string_schema(),
            "amount": _money_schema(),
            "currency": _string_schema(),
            "balance_before": _money_schema(),
            "balance_after": _money_schema(),
            "reason": _string_schema(),
        },
        required=(
            "wallet_id",
            "user_id",
            "ride_id",
            "organization_id",
            "amount",
            "currency",
            "balance_before",
            "balance_after",
            "reason",
        ),
    ),
    "wallet.credited.v1": _object_schema(
        {
            "wallet_id": _string_schema(),
            "user_id": _string_schema(),
            "ride_id": _string_schema(),
            "organization_id": _string_schema(),
            "amount": _money_schema(),
            "currency": _string_schema(),
            "balance_before": _money_schema(),
            "balance_after": _money_schema(),
            "reason": _string_schema(),
        },
        required=(
            "wallet_id",
            "user_id",
            "ride_id",
            "organization_id",
            "amount",
            "currency",
            "balance_before",
            "balance_after",
            "reason",
        ),
    ),
    "transaction.recorded.v1": _object_schema(
        {
            "transaction_id": _string_schema(),
            "wallet_id": _string_schema(),
            "ride_id": _string_schema(),
            "organization_id": _string_schema(),
            "direction": _string_schema(),
            "amount": _money_schema(),
            "currency": _string_schema(),
            "status": _string_schema(),
        },
        required=(
            "transaction_id",
            "wallet_id",
            "ride_id",
            "organization_id",
            "direction",
            "amount",
            "currency",
            "status",
        ),
    ),
    "policy.decision_recorded.v1": _object_schema(
        {
            "decision_id": _string_schema(),
            "organization_id": _string_schema(),
            "action": _string_schema(),
            "subject_id": _string_schema(),
            "resource_id": _string_schema(),
            "outcome": _string_schema(),
            "reason": _string_schema(),
            "policy_version": _string_schema(),
            "rule_ids": _array_schema({"type": "string"}, unique=True),
        },
        required=(
            "decision_id",
            "organization_id",
            "action",
            "subject_id",
            "resource_id",
            "outcome",
            "reason",
            "policy_version",
            "rule_ids",
        ),
    ),
    "approval.requested.v1": _object_schema(
        {
            "approval_id": _string_schema(),
            "organization_id": _string_schema(),
            "action": _string_schema(),
            "requested_by": _string_schema(),
            "reason": _string_schema(),
            "status": _string_schema(),
        },
        required=("approval_id", "organization_id", "action", "requested_by", "reason", "status"),
    ),
    "approval.granted.v1": _object_schema(
        {
            "approval_id": _string_schema(),
            "organization_id": _string_schema(),
            "action": _string_schema(),
            "approved_by": _string_schema(),
            "reason": _string_schema(),
            "status": _string_schema(),
        },
        required=("approval_id", "organization_id", "action", "approved_by", "reason", "status"),
    ),
    "approval.rejected.v1": _object_schema(
        {
            "approval_id": _string_schema(),
            "organization_id": _string_schema(),
            "action": _string_schema(),
            "rejected_by": _string_schema(),
            "reason": _string_schema(),
            "status": _string_schema(),
        },
        required=("approval_id", "organization_id", "action", "rejected_by", "reason", "status"),
    ),
    "trust.score_updated.v1": _object_schema(
        {
            "subject_id": _string_schema(),
            "subject_type": _string_schema(),
            "organization_id": _string_schema(),
            "trust_score": _integer_schema(minimum=0),
            "previous_trust_score": _integer_schema(minimum=0),
            "reason": _string_schema(),
            "signals": _array_schema({"type": "string"}),
        },
        required=(
            "subject_id",
            "subject_type",
            "organization_id",
            "trust_score",
            "previous_trust_score",
            "reason",
            "signals",
        ),
    ),
    "compliance.decision_recorded.v1": _object_schema(
        {
            "compliance_id": _string_schema(),
            "subject_id": _string_schema(),
            "subject_type": _string_schema(),
            "organization_id": _string_schema(),
            "outcome": _string_schema(),
            "reason": _string_schema(),
            "risk_level": _string_schema(),
            "checks": _array_schema({"type": "string"}, unique=True),
        },
        required=(
            "compliance_id",
            "subject_id",
            "subject_type",
            "organization_id",
            "outcome",
            "reason",
            "risk_level",
            "checks",
        ),
    ),
    "inspection.completed.v1": _object_schema(
        {
            "inspection_id": _string_schema(),
            "driver_id": _string_schema(),
            "vehicle_id": _string_schema(),
            "inspector_id": _string_schema(),
            "organization_id": _string_schema(),
            "status": _string_schema(),
            "checklist": {"type": "object", "additionalProperties": True},
            "issues": _array_schema({"type": "string"}),
            "evidence_refs": _array_schema({"type": "string"}),
        },
        required=(
            "inspection_id",
            "driver_id",
            "vehicle_id",
            "inspector_id",
            "organization_id",
            "status",
            "checklist",
            "issues",
            "evidence_refs",
        ),
    ),
    "support.ticket_created.v1": _object_schema(
        {
            "ticket_id": _string_schema(),
            "organization_id": _string_schema(),
            "created_by": _string_schema(),
            "category": _string_schema(),
            "subject_id": _string_schema(),
            "status": _string_schema(),
        },
        required=("ticket_id", "organization_id", "created_by", "category", "subject_id", "status"),
    ),
    "support.dispute_opened.v1": _object_schema(
        {
            "ticket_id": _string_schema(),
            "organization_id": _string_schema(),
            "opened_by": _string_schema(),
            "ride_id": _string_schema(),
            "reason": _string_schema(),
            "status": _string_schema(),
        },
        required=("ticket_id", "organization_id", "opened_by", "ride_id", "reason", "status"),
    ),
    "support.refund_requested.v1": _object_schema(
        {
            "refund_id": _string_schema(),
            "ticket_id": _string_schema(),
            "ride_id": _string_schema(),
            "organization_id": _string_schema(),
            "amount": _money_schema(),
            "currency": _string_schema(),
            "reason": _string_schema(),
            "status": _string_schema(),
        },
        required=("refund_id", "ticket_id", "ride_id", "organization_id", "amount", "currency", "reason", "status"),
    ),
    "support.refund_processed.v1": _object_schema(
        {
            "refund_id": _string_schema(),
            "ticket_id": _string_schema(),
            "ride_id": _string_schema(),
            "organization_id": _string_schema(),
            "amount": _money_schema(),
            "currency": _string_schema(),
            "processed_by": _string_schema(),
            "status": _string_schema(),
        },
        required=("refund_id", "ticket_id", "ride_id", "organization_id", "amount", "currency", "processed_by", "status"),
    ),
    "receipt.issued.v1": _object_schema(
        {
            "receipt_id": _string_schema(),
            "payment_id": _string_schema(),
            "ride_id": _string_schema(),
            "organization_id": _string_schema(),
            "receipt_hash": _string_schema(),
            "status": _string_schema(),
        },
        required=("receipt_id", "payment_id", "ride_id", "organization_id", "receipt_hash", "status"),
    ),
    "receipt.verified.v1": _object_schema(
        {
            "receipt_id": _string_schema(),
            "ride_id": _string_schema(),
            "organization_id": _string_schema(),
            "receipt_hash": _string_schema(),
            "valid": _boolean_schema(),
            "reason": _string_schema(),
        },
        required=("receipt_id", "ride_id", "organization_id", "receipt_hash", "valid", "reason"),
    ),
    "public.verification.completed.v1": _object_schema(
        {
            "verification_id": _string_schema(),
            "receipt_id": _string_schema(),
            "organization_id": _string_schema(),
            "valid": _boolean_schema(),
            "reason": _string_schema(),
            "status": _string_schema(),
        },
        required=("verification_id", "receipt_id", "organization_id", "valid", "reason", "status"),
    ),
    "audit.recorded.v1": _object_schema(
        {
            "audit_id": _string_schema(),
            "organization_id": _string_schema(),
            "actor_id": _string_schema(),
            "action": _string_schema(),
            "object_type": _string_schema(),
            "object_id": _string_schema(),
            "hash": _string_schema(),
            "signature": _string_schema(),
        },
        required=("audit_id", "organization_id", "actor_id", "action", "object_type", "object_id", "hash", "signature"),
    ),
}


class SchemaRegistry:
    """Load, validate, and certify the NovaRide event registry."""

    def __init__(self, registry_path: Path | str | None = None) -> None:
        configured_path = registry_path or os.getenv(
            "AFRITECH_EVENT_REGISTRY_PATH",
            str(EVENT_REGISTRY_PATH),
        )
        self.registry_path = Path(configured_path)
        self._registry = self._load_registry()
        self._entries = {
            item.event_type: item for item in self._registry_entries()
        }

    def _load_registry(self) -> dict[str, Any]:
        if not self.registry_path.is_file():
            raise SchemaRegistryError(f"missing_registry:{self.registry_path}")
        payload = yaml.safe_load(self.registry_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise SchemaRegistryError("registry_must_be_a_mapping")
        required = {"registry_id", "status", "classification", "entries"}
        missing = sorted(required - set(payload))
        if missing:
            raise SchemaRegistryError(f"registry_missing_fields:{missing}")
        if str(payload["registry_id"]) != EVENT_REGISTRY_ID:
            raise SchemaRegistryError("registry_id_mismatch")
        if str(payload["status"]).strip().upper() != "ACTIVE":
            raise SchemaRegistryError("registry_inactive")
        entries = payload.get("entries")
        if not isinstance(entries, list) or not entries:
            raise SchemaRegistryError("registry_entries_required")
        return payload

    def _registry_entries(self) -> tuple[SchemaRegistryEntry, ...]:
        entries: list[SchemaRegistryEntry] = []
        for raw in self._registry["entries"]:
            if not isinstance(raw, Mapping):
                raise SchemaRegistryError("registry_entry_must_be_mapping")
            entry = SchemaRegistryEntry(
                event_type=str(raw["event_type"]),
                domain=str(raw["domain"]),
                owner_service=str(raw["owner_service"]),
                schema_version=int(raw["schema_version"]),
                compatibility=str(raw["compatibility"]),
                status=str(raw["status"]),
                partition_key_strategy=str(raw["partition_key_strategy"]),
                idempotency_strategy=str(raw["idempotency_strategy"]),
                decision_trace_required=bool(raw["decision_trace_required"]),
            )
            entries.append(entry)
        return tuple(entries)

    @property
    def registry(self) -> dict[str, Any]:
        return copy.deepcopy(self._registry)

    @property
    def entries(self) -> tuple[SchemaRegistryEntry, ...]:
        return tuple(self._entries.values())

    def event_types(self) -> tuple[str, ...]:
        return tuple(sorted(self._entries))

    def lookup(self, event_type: str, *, allow_deprecated: bool = False) -> SchemaRegistryEntry:
        entry = self._entries.get(event_type)
        if entry is None:
            raise SchemaRegistryError(f"unknown_event_type:{event_type}")
        allowed_statuses = {"active", "deprecated"} if allow_deprecated else {"active"}
        if entry.status.strip().lower() not in allowed_statuses:
            raise SchemaRegistryError(f"event_type_not_active:{event_type}")
        return entry

    def generate_json_schema(self, event_type: str) -> dict[str, Any]:
        entry = self.lookup(event_type, allow_deprecated=True)
        payload_schema = self._payload_schema(event_type)
        schema = {
            "$schema": EVENT_SCHEMA_DRAFT,
            "$id": self._schema_id(entry),
            "title": event_type,
            "type": "object",
            "required": [
                "event_id",
                "event_type",
                "schema_version",
                "occurred_at",
                "recorded_at",
                "tenant_id",
                "organization_id",
                "subject",
                "actor",
                "resource",
                "correlation_id",
                "causation_id",
                "idempotency_key",
                "sequence",
                "partition_key",
                "source",
                "visibility",
                "decision_trace",
                "schema_ref",
                "payload",
            ],
            "properties": {
                "event_id": _string_schema(),
                "event_type": {"const": event_type},
                "schema_version": {"const": entry.schema_version},
                "occurred_at": {"type": "string"},
                "recorded_at": {"type": "string"},
                "tenant_id": _string_schema(),
                "organization_id": _string_schema(),
                "subject": _object_schema(
                    {"type": _string_schema(), "id": _string_schema()},
                    required=("type", "id"),
                ),
                "actor": _object_schema(
                    {
                        "type": _string_schema(),
                        "id": _string_schema(),
                        "role": _string_schema(),
                    },
                    required=("type", "id", "role"),
                ),
                "resource": _object_schema(
                    {"type": _string_schema(), "id": _string_schema()},
                    required=("type", "id"),
                ),
                "correlation_id": _string_schema(),
                "causation_id": _string_schema(),
                "idempotency_key": _string_schema(),
                "sequence": _integer_schema(minimum=0),
                "partition_key": _string_schema(),
                "source": _string_schema(),
                "visibility": {
                    "type": "string",
                    "enum": ["tenant", "public", "internal", "restricted"],
                },
                "decision_trace": _decision_trace_schema(required=entry.decision_trace_required),
                "schema_ref": _object_schema(
                    {
                        "registry_id": {"const": EVENT_REGISTRY_ID},
                        "document_id": {"type": "string"},
                        "revision": _string_schema(),
                    },
                    required=("registry_id", "document_id", "revision"),
                ),
                "payload": payload_schema,
            },
            "additionalProperties": False,
        }
        Draft202012Validator.check_schema(schema)
        return schema

    def generate_json_schema_catalog(self) -> dict[str, Any]:
        return {
            "registry_id": EVENT_REGISTRY_ID,
            "schemas": {
                event_type: self.generate_json_schema(event_type)
                for event_type in self.event_types()
            },
        }

    def write_json_schema_catalog(self, output_dir: Path | str = EVENT_SCHEMA_OUTPUT_DIR) -> list[Path]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        paths: list[Path] = []
        for event_type in self.event_types():
            target = output_path / f"{event_type}.schema.json"
            target.write_text(
                json.dumps(self.generate_json_schema(event_type), indent=2, sort_keys=True),
                encoding="utf-8",
            )
            paths.append(target)
        return paths

    def schema_digest(self, event_type: str) -> str:
        schema = self.generate_json_schema(event_type)
        canonical = json.dumps(schema, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def schema_publication(self, event_type: str) -> dict[str, Any]:
        entry = self.lookup(event_type, allow_deprecated=True)
        publication = {
            "registry_id": EVENT_REGISTRY_ID,
            "event_type": event_type,
            "schema_id": self._schema_id(entry),
            "schema_version": entry.schema_version,
            "schema_digest": self.schema_digest(event_type),
            "compatibility": entry.compatibility,
            "status": entry.status.upper(),
            "decision_trace_required": entry.decision_trace_required,
        }
        try:
            signature = sign_packet(publication).canonical()
        except Exception as exc:  # pragma: no cover - defensive production path
            raise SchemaRegistryError(
                f"schema_publication_signing_failed:{event_type}:{type(exc).__name__}"
            ) from exc
        return {**publication, "signature": signature}

    def certification_check(self, event_type: str) -> dict[str, Any]:
        try:
            publication = self.schema_publication(event_type)
            signed = {
                key: publication[key]
                for key in (
                    "registry_id",
                    "event_type",
                    "schema_id",
                    "schema_version",
                    "schema_digest",
                    "compatibility",
                    "status",
                    "decision_trace_required",
                )
            }
            signature = publication["signature"]
            valid_signature = verify_packet_signature(signed, signature)
            entry = self.lookup(event_type, allow_deprecated=True)
            certified = bool(valid_signature and entry.certified)
            reason = "certified" if certified else "registry_or_signature_invalid"
        except SchemaRegistryError as exc:
            certified = False
            reason = str(exc)
            publication = {
                "registry_id": EVENT_REGISTRY_ID,
                "event_type": event_type,
                "schema_id": None,
                "schema_version": None,
                "schema_digest": None,
                "compatibility": None,
                "status": None,
                "decision_trace_required": None,
                "signature": None,
            }
        return {
            "event_type": event_type,
            "certified": certified,
            "reason": reason,
            "publication": publication,
        }

    def require_certified(self, event_type: str) -> dict[str, Any]:
        result = self.certification_check(event_type)
        if not result["certified"]:
            raise SchemaRegistryError(f"schema_not_certified:{event_type}:{result['reason']}")
        return result

    def validate_event(self, event: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(event, Mapping):
            raise SchemaRegistryError("event_must_be_mapping")
        event_type = str(event.get("event_type", ""))
        entry = self.lookup(event_type)
        self.require_certified(event_type)
        self._validate_registry_metadata(event, entry)
        schema = self.generate_json_schema(event_type)
        errors = sorted(
            Draft202012Validator(schema).iter_errors(dict(event)),
            key=lambda error: tuple(str(item) for item in error.absolute_path),
        )
        if errors:
            detail = "; ".join(error.message for error in errors)
            raise SchemaRegistryError(f"event_schema_invalid:{event_type}:{detail}")
        self._validate_decision_trace(event, entry)
        return {
            "valid": True,
            "event_type": event_type,
            "schema_version": entry.schema_version,
            "publication": self.schema_publication(event_type),
        }

    def validate_batch(self, events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
        accepted: list[str] = []
        rejected: list[dict[str, str]] = []
        for event in events:
            try:
                result = self.validate_event(event)
                accepted.append(str(result["event_type"]))
            except SchemaRegistryError as exc:
                rejected.append(
                    {
                        "event_type": str(event.get("event_type", "")) if isinstance(event, Mapping) else "",
                        "reason": str(exc),
                    }
                )
        return {
            "accepted": accepted,
            "rejected": rejected,
            "all_valid": not rejected,
        }

    def compatibility_report(
        self,
        previous_event_type: str,
        current_event_type: str,
    ) -> CompatibilityReport:
        previous = self.generate_json_schema(previous_event_type)
        current = self.generate_json_schema(current_event_type)
        return self.compare_schemas(previous, current)

    def compare_schemas(
        self,
        previous_schema: Mapping[str, Any],
        current_schema: Mapping[str, Any],
    ) -> CompatibilityReport:
        breaking: list[str] = []
        warnings: list[str] = []
        backward = True
        forward = True

        previous_properties = _properties(previous_schema)
        current_properties = _properties(current_schema)
        previous_required = set(previous_schema.get("required", ()))
        current_required = set(current_schema.get("required", ()))

        removed_properties = sorted(set(previous_properties) - set(current_properties))
        added_properties = sorted(set(current_properties) - set(previous_properties))
        if removed_properties:
            backward = False
            forward = False
            breaking.append(f"removed_properties:{removed_properties}")

        added_required = sorted(current_required - previous_required)
        if added_required:
            backward = False
            breaking.append(f"added_required:{added_required}")

        previous_additional = bool(previous_schema.get("additionalProperties", True))
        current_additional = bool(current_schema.get("additionalProperties", True))
        if previous_additional is False and current_additional is True:
            warnings.append("current_schema_more_permissive")
        if previous_additional is True and current_additional is False and added_properties:
            forward = False
            breaking.append("current_schema_rejects_unknown_fields")

        for name in sorted(set(previous_properties) & set(current_properties)):
            compare = _compare_schema_nodes(
                previous_properties[name],
                current_properties[name],
                path=(name,),
            )
            breaking.extend(compare.breaking_changes)
            warnings.extend(compare.warnings)
            backward = backward and compare.backward_compatible
            forward = forward and compare.forward_compatible

        return CompatibilityReport(
            backward_compatible=backward,
            forward_compatible=forward,
            breaking_changes=tuple(breaking),
            warnings=tuple(warnings),
        )

    def validate_compatibility(
        self,
        previous_event_type: str,
        current_event_type: str,
    ) -> CompatibilityReport:
        report = self.compatibility_report(previous_event_type, current_event_type)
        if not report.backward_compatible:
            raise SchemaRegistryError(
                f"incompatible_event_schema:{previous_event_type}->{current_event_type}:{list(report.breaking_changes)}"
            )
        return report

    def _schema_id(self, entry: SchemaRegistryEntry) -> str:
        return f"https://novaride.example/contracts/{entry.event_type}/{entry.schema_version}.0"

    def _payload_schema(self, event_type: str) -> dict[str, Any]:
        schema = EVENT_PAYLOAD_SCHEMAS.get(event_type)
        if schema is None:
            return {
                "type": "object",
                "additionalProperties": True,
            }
        return copy.deepcopy(schema)

    def _validate_decision_trace(self, event: Mapping[str, Any], entry: SchemaRegistryEntry) -> None:
        decision_trace = event.get("decision_trace")
        if not isinstance(decision_trace, Mapping):
            raise SchemaRegistryError(f"decision_trace_must_be_object:{entry.event_type}")
        if entry.decision_trace_required:
            required = ("policy_id", "policy_version", "rule_ids", "flag_evaluations", "evaluation_result")
            missing = [key for key in required if key not in decision_trace]
            if missing:
                raise SchemaRegistryError(
                    f"decision_trace_missing_fields:{entry.event_type}:{missing}"
                )
            if not decision_trace.get("policy_id") or not decision_trace.get("policy_version"):
                raise SchemaRegistryError(
                    f"decision_trace_must_include_policy:{entry.event_type}"
                )
            rule_ids = decision_trace.get("rule_ids")
            if not isinstance(rule_ids, list) or not rule_ids:
                raise SchemaRegistryError(
                    f"decision_trace_rule_ids_required:{entry.event_type}"
                )

    def _validate_registry_metadata(self, event: Mapping[str, Any], entry: SchemaRegistryEntry) -> None:
        schema_ref = event.get("schema_ref")
        if not isinstance(schema_ref, Mapping):
            raise SchemaRegistryError(f"schema_ref_required:{entry.event_type}")
        if schema_ref.get("registry_id") != EVENT_REGISTRY_ID:
            raise SchemaRegistryError(f"registry_lookup_enforcement_failed:{entry.event_type}")
        document_id = str(schema_ref.get("document_id", "")).strip()
        revision = str(schema_ref.get("revision", "")).strip()
        if document_id == "":
            raise SchemaRegistryError(f"schema_ref_document_id_required:{entry.event_type}")
        if document_id != entry.event_type:
            raise SchemaRegistryError(f"schema_ref_document_id_mismatch:{entry.event_type}:{document_id}")
        if revision == "":
            raise SchemaRegistryError(f"schema_ref_revision_required:{entry.event_type}")
        if revision not in {str(entry.schema_version), f"{entry.schema_version}.0"}:
            raise SchemaRegistryError(f"schema_ref_revision_mismatch:{entry.event_type}:{revision}")


def _properties(schema: Mapping[str, Any]) -> dict[str, Any]:
    properties = schema.get("properties", {})
    if not isinstance(properties, Mapping):
        return {}
    return dict(properties)


def _type_set(node: Mapping[str, Any]) -> set[str]:
    value = node.get("type")
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return {str(item) for item in value}
    return set()


def _compare_schema_nodes(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
    *,
    path: tuple[str, ...],
) -> CompatibilityReport:
    breaking: list[str] = []
    warnings: list[str] = []
    backward = True
    forward = True

    previous_types = _type_set(previous)
    current_types = _type_set(current)
    if previous_types and current_types and previous_types != current_types:
        backward = False
        forward = False
        breaking.append(f"type_change:{'.'.join(path)}:{sorted(previous_types)}->{sorted(current_types)}")

    previous_enum = set(previous.get("enum", ()))
    current_enum = set(current.get("enum", ()))
    if previous_enum and current_enum:
        if not previous_enum.issubset(current_enum):
            backward = False
            breaking.append(f"enum_narrowed:{'.'.join(path)}")
        if not current_enum.issubset(previous_enum):
            forward = False

    previous_required = set(previous.get("required", ()))
    current_required = set(current.get("required", ()))
    if previous_required - current_required:
        warnings.append(f"required_removed:{'.'.join(path)}")
    if current_required - previous_required:
        backward = False
        breaking.append(f"required_added:{'.'.join(path)}:{sorted(current_required - previous_required)}")

    previous_additional = previous.get("additionalProperties", True)
    current_additional = current.get("additionalProperties", True)
    if previous_additional is False and current_additional is True:
        warnings.append(f"additional_properties_relaxed:{'.'.join(path)}")
    if previous_additional is True and current_additional is False:
        forward = False
        if previous.get("properties") or current.get("properties"):
            breaking.append(f"additional_properties_tightened:{'.'.join(path)}")

    previous_props = _properties(previous)
    current_props = _properties(current)
    removed_props = sorted(set(previous_props) - set(current_props))
    added_props = sorted(set(current_props) - set(previous_props))
    if removed_props:
        backward = False
        forward = False
        breaking.append(f"nested_removed_properties:{'.'.join(path)}:{removed_props}")
    if added_props and previous_additional is False:
        forward = False
        breaking.append(f"nested_added_properties:{'.'.join(path)}:{added_props}")

    for name in sorted(set(previous_props) & set(current_props)):
        nested = _compare_schema_nodes(
            previous_props[name],
            current_props[name],
            path=path + (name,),
        )
        breaking.extend(nested.breaking_changes)
        warnings.extend(nested.warnings)
        backward = backward and nested.backward_compatible
        forward = forward and nested.forward_compatible

    return CompatibilityReport(
        backward_compatible=backward,
        forward_compatible=forward,
        breaking_changes=tuple(breaking),
        warnings=tuple(warnings),
    )


def build_schema_registry() -> SchemaRegistry:
    return SchemaRegistry()


def build_schema_catalog() -> dict[str, Any]:
    return build_schema_registry().generate_json_schema_catalog()


__all__ = [
    "CompatibilityReport",
    "EVENT_REGISTRY_ID",
    "EVENT_REGISTRY_PATH",
    "EVENT_SCHEMA_OUTPUT_DIR",
    "SchemaRegistry",
    "SchemaRegistryEntry",
    "SchemaRegistryError",
    "build_schema_catalog",
    "build_schema_registry",
]
