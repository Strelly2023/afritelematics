from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from afritech.security.mutation_guard import FORBIDDEN_MUTATION_FIELDS


class EventContractRules:
    """Constitutional rules beyond JSON Schema shape validation."""

    def __init__(self) -> None:
        self.last_clock: dict[str, int] = {}
        self.seen_event_ids: set[str] = set()

    def validate_logical_clock(self, event: Mapping[str, Any]) -> None:
        device = str(event["device_id"])
        clock = int(event["logical_clock"])

        last = self.last_clock.get(device, -1)
        if clock <= last:
            raise ValueError("logical_clock_regression")

        self.last_clock[device] = clock

    def validate_duplicate(self, event: Mapping[str, Any]) -> None:
        event_id = str(event["event_id"])
        if event_id in self.seen_event_ids:
            raise ValueError("duplicate_event")
        self.seen_event_ids.add(event_id)

    def validate_payload(self, event: Mapping[str, Any]) -> None:
        if not isinstance(event["payload"], Mapping):
            raise ValueError("invalid_structure")

    def validate_forbidden_fields(self, event: Mapping[str, Any]) -> None:
        if _contains_forbidden_authority_field(event):
            raise ValueError("forbidden_authority_field")

    def validate(self, event: Mapping[str, Any]) -> None:
        self.validate_payload(event)
        self.validate_forbidden_fields(event)
        self.validate_duplicate(event)
        self.validate_logical_clock(event)


def _contains_forbidden_authority_field(value: Mapping[str, Any]) -> bool:
    if FORBIDDEN_MUTATION_FIELDS.intersection(value.keys()):
        return True
    for nested in value.values():
        if isinstance(nested, Mapping) and _contains_forbidden_authority_field(nested):
            return True
        if isinstance(nested, list):
            for item in nested:
                if isinstance(item, Mapping) and _contains_forbidden_authority_field(item):
                    return True
    return False
