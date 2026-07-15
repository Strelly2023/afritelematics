"""Event schema compatibility checks."""

from __future__ import annotations

from dataclasses import dataclass

from afritech.novaride_runtime.events.schema_registry import EventSchema


@dataclass(frozen=True, slots=True)
class CompatibilityResult:
    compatible: bool
    reason: str


def check_compatible(previous: EventSchema, current: EventSchema) -> CompatibilityResult:
    if previous.event_type != current.event_type:
        return CompatibilityResult(False, "event_type_changed")
    removed_required = set(previous.required_payload_fields) - set(current.required_payload_fields)
    if removed_required:
        return CompatibilityResult(False, "required_field_removed")
    if previous.aggregate_type != current.aggregate_type:
        return CompatibilityResult(False, "aggregate_type_changed")
    return CompatibilityResult(True, "compatible_additive")
