"""Breaking-change analysis for stable OpenAPI contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BreakingChange:
    code: str
    location: str
    message: str
    severity: str = "error"


def _operations(spec: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() in {"get", "post", "put", "patch", "delete", "options", "head"}:
                result[(method.upper(), path)] = operation
    return result


def _schemas(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return spec.get("components", {}).get("schemas", {})


def detect_breaking_changes(previous: dict[str, Any], current: dict[str, Any]) -> list[BreakingChange]:
    changes: list[BreakingChange] = []
    previous_operations = _operations(previous)
    current_operations = _operations(current)
    for key in previous_operations:
        if key not in current_operations:
            method, path = key
            changes.append(BreakingChange("OPERATION_REMOVED", f"{method} {path}", "A previously published operation was removed."))
    previous_schemas = _schemas(previous)
    current_schemas = _schemas(current)
    for schema_name, old_schema in previous_schemas.items():
        new_schema = current_schemas.get(schema_name)
        if new_schema is None:
            changes.append(BreakingChange("SCHEMA_REMOVED", schema_name, "A previously published schema was removed."))
            continue
        old_properties = old_schema.get("properties", {})
        new_properties = new_schema.get("properties", {})
        for property_name, old_property in old_properties.items():
            if property_name not in new_properties:
                changes.append(BreakingChange("PROPERTY_REMOVED", f"{schema_name}.{property_name}", "A response property was removed."))
                continue
            new_property = new_properties[property_name]
            if old_property.get("type") != new_property.get("type"):
                changes.append(
                    BreakingChange(
                        "PROPERTY_TYPE_CHANGED",
                        f"{schema_name}.{property_name}",
                        f"Type changed from {old_property.get('type')} to {new_property.get('type')}.",
                    )
                )
        old_required = set(old_schema.get("required", []))
        new_required = set(new_schema.get("required", []))
        for added_required in sorted(new_required - old_required):
            changes.append(BreakingChange("REQUIRED_PROPERTY_ADDED", f"{schema_name}.{added_required}", "A required property was added."))
    return changes
