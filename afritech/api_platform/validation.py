"""Request/response validation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .errors import ApiValidationError


@dataclass
class SchemaRegistry:
    validators: dict[str, Any] = field(default_factory=dict)

    def register(self, schema_name: str, validator: Any) -> None:
        self.validators[schema_name] = validator

    def validate(self, schema_name: str | None, payload: Mapping[str, Any]) -> None:
        if schema_name is None:
            return
        validator = self.validators.get(schema_name)
        if validator is None:
            return
        if callable(validator):
            result = validator(payload)
            if result is False:
                raise ApiValidationError(f"schema_validation_failed:{schema_name}")
            return
        raise ApiValidationError(f"unknown_schema_validator:{schema_name}")
