from __future__ import annotations

from typing import Callable, Mapping, Any

import jsonschema

from afritech.state.state import State
from afritech.state.types import JSONValue
from afritech.guards.engine import GuardResult, Guard


# ---------------------------------------------------------------------
# Schema loader (pure, deterministic)
# ---------------------------------------------------------------------

def _validate_schema(data: Mapping[str, JSONValue], schema: Mapping[str, Any]) -> list[str]:
    """
    Validate data against JSON Schema.
    Returns list of violation messages (empty if valid).
    """

    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

    return [e.message for e in errors]


# ---------------------------------------------------------------------
# Generic schema guard factory
# ---------------------------------------------------------------------

def make_schema_guard(
    schema: Mapping[str, Any],
    selector: Callable[[State], Mapping[str, JSONValue]],
    violation_code: str,
) -> Guard:
    """
    Create a guard that validates part of the State against a schema.

    - selector extracts the portion of State to validate
    - schema defines admissible structure
    """

    def guard(state: State, transition) -> GuardResult:
        candidate = transition(state)

        data = selector(candidate)
        violations = _validate_schema(data, schema)

        if violations:
            return GuardResult(
                ok=False,
                reason=f"{violation_code}:{'|'.join(violations)}"
            )

        return GuardResult(True)

    return guard


# ---------------------------------------------------------------------
# Concrete schema guards
# ---------------------------------------------------------------------

def registry_schema_guard(schema: Mapping[str, Any]) -> Guard:
    return make_schema_guard(
        schema=schema,
        selector=lambda s: s.registry.payload,
        violation_code="REGISTRY_SCHEMA_VIOLATION",
    )


def vm_schema_guard(schema: Mapping[str, Any]) -> Guard:
    return make_schema_guard(
        schema=schema,
        selector=lambda s: s.vm.payload,
        violation_code="VM_SCHEMA_VIOLATION",
    )


def governance_schema_guard(schema: Mapping[str, Any]) -> Guard:
    return make_schema_guard(
        schema=schema,
        selector=lambda s: s.governance.payload,
        violation_code="GOVERNANCE_SCHEMA_VIOLATION",
    )