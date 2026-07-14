"""Runtime OpenAPI response validation."""

from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator, ValidationError


class RuntimeContractViolation(RuntimeError):
    pass


def validate_payload(payload: Any, schema: dict[str, Any], *, operation_id: str) -> None:
    try:
        Draft202012Validator(schema).validate(payload)
    except ValidationError as exc:
        raise RuntimeContractViolation(f"Response violated contract for {operation_id}: {exc.message}") from exc
