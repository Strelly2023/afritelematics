from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, RefResolver, ValidationError


CONTRACT_DIR = Path(__file__).resolve().parent


class EventContractValidator:
    """JSON Schema validator for the canonical mobile event contract."""

    def __init__(self) -> None:
        self.event_schema = self._load_schema("event.schema.json")
        self.batch_schema = self._load_schema("event_batch.schema.json")
        resolver = RefResolver(
            base_uri=CONTRACT_DIR.as_uri() + "/",
            referrer=self.batch_schema,
        )
        self.event_validator = Draft7Validator(self.event_schema)
        self.batch_validator = Draft7Validator(self.batch_schema, resolver=resolver)

    def validate_event(self, event: Any) -> None:
        self.event_validator.validate(event)

    def validate_batch(self, payload: Any) -> None:
        self.batch_validator.validate(payload)

    def event_error(self, event: Any) -> str | None:
        try:
            self.validate_event(event)
        except ValidationError:
            return "invalid_event_type" if _looks_like_bad_event_type(event) else "invalid_structure"
        return None

    def batch_error(self, payload: Any) -> str | None:
        try:
            self.validate_batch(payload)
        except ValidationError:
            return "invalid_request"
        return None

    def _load_schema(self, filename: str) -> dict[str, Any]:
        schema_path = CONTRACT_DIR / filename
        payload = json.loads(schema_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{filename} must contain a JSON object")
        return payload


def _looks_like_bad_event_type(event: Any) -> bool:
    if not isinstance(event, dict):
        return False
    event_type = event.get("event_type")
    return isinstance(event_type, str) and event_type == "INVALID"
