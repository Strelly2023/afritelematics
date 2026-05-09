# afritech/guards/schema.py

from __future__ import annotations

from typing import Callable, Mapping, Any, List

import jsonschema

from afritech.state.state import State
from afritech.state.types import JSONValue
from afritech.guards.guard_core import GuardResult
from afritech.guards.engine import fail, ViolationClass


# ---------------------------------------------------------------------
# Schema validator (pure, deterministic)
# ---------------------------------------------------------------------

def _validate_schema(
    data: Mapping[str, JSONValue],
    schema: Mapping[str, Any],
) -> List[str]:
    """
    Validate data against JSON Schema.

    Returns:
        list[str] → error messages (empty if valid)

    Deterministic:
    - sorted errors
    - no randomness
    """

    validator = jsonschema.Draft202012Validator(schema)

    errors = sorted(
        validator.iter_errors(data),
        key=lambda e: list(e.path),
    )

    return [e.message for e in errors]


# ---------------------------------------------------------------------
# Enforcement bridge
# ---------------------------------------------------------------------

def _enforce(result: GuardResult):
    """
    Convert GuardResult into constitutional failure
    """

    if not result.ok:
        fail(
            result.reason or "schema_violation",
            ViolationClass.B_STRUCTURAL,
        )


# ---------------------------------------------------------------------
# Generic schema guard factory
# ---------------------------------------------------------------------

def make_schema_guard(
    schema: Mapping[str, Any],
    selector: Callable[[State], Mapping[str, JSONValue]],
    violation_code: str,
):
    """
    Create an enforcing schema guard.

    Design:
    - functional validation → GuardResult
    - enforcement → fail()

    selector:
        extracts portion of state to validate
    """

    def guard(state: State, transition):

        candidate = transition(state)

        data = selector(candidate)

        # Structural sanity check (fast fail)
        if not isinstance(data, Mapping):
            fail(
                f"{violation_code}:invalid_data_structure",
                ViolationClass.B_STRUCTURAL,
            )

        violations = _validate_schema(data, schema)

        if violations:
            result = GuardResult(
                ok=False,
                reason=f"{violation_code}:{'|'.join(violations)}",
            )
        else:
            result = GuardResult(True)

        _enforce(result)

        return True

    return guard


# ---------------------------------------------------------------------
# Concrete schema guards
# ---------------------------------------------------------------------

def registry_schema_guard(schema: Mapping[str, Any]):
    return make_schema_guard(
        schema=schema,
        selector=lambda s: s.registry.payload,
        violation_code="REGISTRY_SCHEMA_VIOLATION",
    )


def vm_schema_guard(schema: Mapping[str, Any]):
    return make_schema_guard(
        schema=schema,
        selector=lambda s: s.vm.payload,
        violation_code="VM_SCHEMA_VIOLATION",
    )


def governance_schema_guard(schema: Mapping[str, Any]):
    return make_schema_guard(
        schema=schema,
        selector=lambda s: s.governance.payload,
        violation_code="GOVERNANCE_SCHEMA_VIOLATION",
    )


# ---------------------------------------------------------------------
# OPTIONAL: batch schema enforcement
# ---------------------------------------------------------------------

def enforce_all_schema_guards(
    guards,
    state: State,
    transition,
):
    """
    Run multiple schema guards deterministically.
    """

    for g in guards:
        g(state, transition)

    return True