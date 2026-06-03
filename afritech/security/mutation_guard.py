from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


FORBIDDEN_MUTATION_FIELDS = frozenset(
    {
        "replay_hash",
        "replay_id",
        "witness_hash",
        "mutation_witness",
        "constitutional_authority",
    }
)


class MutationGuard:
    """Structure and lineage guard for mutation candidates."""

    def validate(self, event: Mapping[str, Any]) -> bool:
        try:
            self.require_valid(event)
        except ValueError:
            return False
        return True

    def require_valid(self, event: Mapping[str, Any]) -> None:
        required_fields = {"id", "timestamp", "payload"}
        if not required_fields.issubset(event.keys()):
            raise ValueError("Invalid event structure")
        if not isinstance(event["id"], str) or not event["id"]:
            raise ValueError("Invalid event id")
        if not isinstance(event["timestamp"], int):
            raise ValueError("Invalid event timestamp")
        if not isinstance(event["payload"], Mapping):
            raise ValueError("Invalid event payload")

        lineage = event.get("lineage", ())
        if not isinstance(lineage, Sequence) or isinstance(lineage, (str, bytes)):
            raise ValueError("Invalid event lineage")
        if any(not isinstance(item, str) or not item for item in lineage):
            raise ValueError("Invalid event lineage")

        self._reject_authority_injection(event)
        self._reject_authority_injection(event["payload"])

    def _reject_authority_injection(self, value: Mapping[str, Any]) -> None:
        injected = FORBIDDEN_MUTATION_FIELDS.intersection(value.keys())
        if injected:
            field = sorted(injected)[0]
            raise ValueError(f"Forbidden authority field in mutation: {field}")

        for nested in value.values():
            if isinstance(nested, Mapping):
                self._reject_authority_injection(nested)
            elif isinstance(nested, list):
                for item in nested:
                    if isinstance(item, Mapping):
                        self._reject_authority_injection(item)
