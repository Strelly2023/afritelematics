from __future__ import annotations

from pathlib import Path
from typing import Any

from architecture_validator.model import RuleResult, pass_or_fail
from architecture_validator.scanners.openapi_loader import load_openapi


HTTP_METHODS = {"get", "put", "post", "delete", "patch", "options", "head", "trace"}


class SemanticDiff:
    def compare(self, old: dict[str, Any], new: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        issues.extend(self.compare_paths(old, new))
        issues.extend(self.compare_schemas(old, new))
        return issues

    def compare_paths(self, old: dict[str, Any], new: dict[str, Any]) -> list[str]:
        return _diff_paths(old, new)

    def compare_schemas(self, old: dict[str, Any], new: dict[str, Any]) -> list[str]:
        return _diff_component_schemas(old, new)


def diff_openapi_breaking_changes(
    old: dict[str, Any],
    new: dict[str, Any],
) -> list[str]:
    return SemanticDiff().compare(old, new)


def check_openapi_diff(config: dict[str, object]) -> RuleResult:
    old_path = str(config.get("openapi_baseline_path") or "")
    new_path = str(config.get("openapi_current_path") or "")
    if not old_path or not new_path:
        return pass_or_fail("Semantic OpenAPI Diff", [])

    if not Path(old_path).exists() or not Path(new_path).exists():
        return pass_or_fail(
            "Semantic OpenAPI Diff",
            [f"Configured OpenAPI diff inputs are missing: {old_path}, {new_path}"],
        )

    return pass_or_fail(
        "Semantic OpenAPI Diff",
        diff_openapi_breaking_changes(load_openapi(old_path), load_openapi(new_path)),
    )


def _diff_paths(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    old_paths = _mapping_at(old, "paths")
    new_paths = _mapping_at(new, "paths")

    for path in sorted(set(old_paths) - set(new_paths)):
        issues.append(f"BREAKING: Removed endpoint {path}")

    for path in sorted(set(old_paths) & set(new_paths)):
        old_methods = _path_methods(old_paths[path])
        new_methods = _path_methods(new_paths[path])
        for method in sorted(set(old_methods) - set(new_methods)):
            issues.append(f"BREAKING: Removed method {method.upper()} {path}")

    return issues


def _diff_component_schemas(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    old_schemas = _mapping_at(_mapping_at(old, "components"), "schemas")
    new_schemas = _mapping_at(_mapping_at(new, "components"), "schemas")

    for name in sorted(set(old_schemas) - set(new_schemas)):
        issues.append(f"BREAKING: Removed schema {name}")

    for name in sorted(set(old_schemas) & set(new_schemas)):
        issues.extend(_diff_schema(name, old_schemas[name], new_schemas[name]))

    return issues


def _diff_schema(name: str, old_schema: object, new_schema: object) -> list[str]:
    issues: list[str] = []
    if not isinstance(old_schema, dict) or not isinstance(new_schema, dict):
        return issues

    old_type = old_schema.get("type")
    new_type = new_schema.get("type")
    if old_type and new_type and old_type != new_type:
        issues.append(f"BREAKING: Schema {name} type changed from {old_type} to {new_type}")

    old_required = set(_string_list(old_schema.get("required")))
    new_required = set(_string_list(new_schema.get("required")))
    for field in sorted(old_required - new_required):
        issues.append(f"BREAKING: Schema {name} no longer requires field {field}")

    old_properties = _mapping_at(old_schema, "properties")
    new_properties = _mapping_at(new_schema, "properties")
    for field in sorted(set(old_properties) - set(new_properties)):
        issues.append(f"BREAKING: Removed field {name}.{field}")

    for field in sorted(set(old_properties) & set(new_properties)):
        old_field = old_properties[field]
        new_field = new_properties[field]
        if isinstance(old_field, dict) and isinstance(new_field, dict):
            old_field_type = old_field.get("type")
            new_field_type = new_field.get("type")
            if old_field_type and new_field_type and old_field_type != new_field_type:
                issues.append(
                    "BREAKING: Field "
                    f"{name}.{field} type changed from {old_field_type} to {new_field_type}"
                )

    return issues


def _mapping_at(payload: object, key: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _path_methods(path_item: object) -> dict[str, Any]:
    if not isinstance(path_item, dict):
        return {}
    return {key: value for key, value in path_item.items() if key.lower() in HTTP_METHODS}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]
