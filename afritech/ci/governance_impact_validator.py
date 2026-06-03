"""
CI validator for the read-only Governance Impact Query.

Constitutional Law
------------------
Governance Impact Query may answer:

    "Which executions reference this governance object?"

It must not:
- execute runtime behavior
- validate runtime truth
- enforce governance
- mutate receipts
- load YAML
- access DB state
- import governance projection
- create runtime, replay, proof, CI, or governance authority
"""

from __future__ import annotations

import ast
import inspect
import sys
from types import ModuleType

from afritech.api import governance_impact_views
from afritech.impact import impact_index, impact_query


class GovernanceImpactValidationError(RuntimeError):
    """Raised when Governance Impact Query violates constitutional law."""


FORBIDDEN_IMPORT_PREFIXES = (
    "afritech.runtime",
    "afritech.execution",
    "afritech.verify",
    "afritech.registry",
    "afritech.proof.constitutional_receipt",
    "afritech.governance_projection",
)

FORBIDDEN_CALL_NAMES = (
    "open",
    "save",
    "delete",
    "safe_load",
    "load",
    "execute",
    "enforce",
    "validate",
    "authorize",
    "admit",
    "decide",
)

FORBIDDEN_MUTATION_ATTRIBUTES = (
    "objects",
    "save",
    "delete",
    "update",
    "create",
)

REQUIRED_FALSE_FLAGS = (
    "RUNTIME_AUTHORITY",
    "ENFORCEMENT_AUTHORITY",
    "VALIDATION_AUTHORITY",
    "REPLAY_AUTHORITY",
    "PROOF_AUTHORITY",
    "CI_AUTHORITY",
    "GOVERNANCE_AUTHORITY",
    "MUTATION_ALLOWED",
)

VIEW_REQUIRED_FALSE_FLAGS = (
    "RUNTIME_AUTHORITY",
    "ENFORCEMENT_AUTHORITY",
    "VALIDATION_AUTHORITY",
    "REPLAY_AUTHORITY",
    "PROOF_AUTHORITY",
    "CI_AUTHORITY",
    "GOVERNANCE_AUTHORITY",
    "MUTATION_ALLOWED",
    "RECEIPT_MUTATION_ALLOWED",
)

REQUIRED_TRUE_FLAGS = (
    "REFERENCE_ONLY",
    "READ_ONLY",
    "DISPLAY_ONLY",
)

VALIDATED_MODULES = (
    impact_index,
    impact_query,
    governance_impact_views,
)


def _fail(message: str) -> None:
    raise GovernanceImpactValidationError(message)


def _source(module: ModuleType) -> str:
    return inspect.getsource(module)


def _tree(module: ModuleType) -> ast.Module:
    return ast.parse(_source(module))


def _validate_forbidden_imports(module: ModuleType) -> None:
    tree = _tree(module)

    for item in ast.walk(tree):
        if isinstance(item, ast.Import):
            for alias in item.names:
                if alias.name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    _fail(
                        f"{module.__name__} has forbidden import "
                        f"{alias.name}"
                    )

        if isinstance(item, ast.ImportFrom):
            module_name = item.module or ""
            if module_name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                _fail(
                    f"{module.__name__} has forbidden import "
                    f"{module_name}"
                )


def _validate_forbidden_calls(module: ModuleType) -> None:
    tree = _tree(module)

    for item in ast.walk(tree):
        if not isinstance(item, ast.Call):
            continue

        func = item.func
        call_name = ""

        if isinstance(func, ast.Name):
            call_name = func.id
        elif isinstance(func, ast.Attribute):
            call_name = func.attr

        if call_name in FORBIDDEN_CALL_NAMES:
            _fail(f"{module.__name__} has forbidden call {call_name}")


def _validate_forbidden_mutation_attributes(module: ModuleType) -> None:
    tree = _tree(module)

    for item in ast.walk(tree):
        if isinstance(item, ast.Attribute):
            if item.attr in FORBIDDEN_MUTATION_ATTRIBUTES:
                _fail(
                    f"{module.__name__} references forbidden mutation "
                    f"attribute {item.attr}"
                )


def _validate_index_flags() -> None:
    if impact_index.IMPACT_INDEX_STATUS != "READ_ONLY_IMPACT_INDEX":
        _fail("IMPACT_INDEX_STATUS must be READ_ONLY_IMPACT_INDEX")

    for flag_name in REQUIRED_TRUE_FLAGS:
        if getattr(impact_index, flag_name, None) is not True:
            _fail(f"impact_index.{flag_name} must be True")

    for flag_name in REQUIRED_FALSE_FLAGS:
        if getattr(impact_index, flag_name, None) is not False:
            _fail(f"impact_index.{flag_name} must be False")

    if impact_index.RECEIPT_MUTATION_ALLOWED is not False:
        _fail("impact_index.RECEIPT_MUTATION_ALLOWED must be False")

    if impact_index.RUNTIME_DEPENDENCY is not False:
        _fail("impact_index.RUNTIME_DEPENDENCY must be False")

    if impact_index.PROJECTION_DEPENDENCY is not False:
        _fail("impact_index.PROJECTION_DEPENDENCY must be False")


def _validate_query_flags() -> None:
    if impact_query.IMPACT_QUERY_STATUS != "READ_ONLY_IMPACT_QUERY":
        _fail("IMPACT_QUERY_STATUS must be READ_ONLY_IMPACT_QUERY")

    if impact_query.QUERY_AUTHORITY is not False:
        _fail("impact_query.QUERY_AUTHORITY must be False")

    if impact_query.DECISION_AUTHORITY is not False:
        _fail("impact_query.DECISION_AUTHORITY must be False")

    if impact_query.ADMISSIBILITY_AUTHORITY is not False:
        _fail("impact_query.ADMISSIBILITY_AUTHORITY must be False")

    if impact_query.MUTATION_ALLOWED is not False:
        _fail("impact_query.MUTATION_ALLOWED must be False")


def _validate_view_flags() -> None:
    if (
        governance_impact_views.GOVERNANCE_IMPACT_API_STATUS
        != "READ_ONLY_GOVERNANCE_IMPACT_API"
    ):
        _fail(
            "GOVERNANCE_IMPACT_API_STATUS must be "
            "READ_ONLY_GOVERNANCE_IMPACT_API"
        )

    for flag_name in REQUIRED_TRUE_FLAGS:
        if getattr(governance_impact_views, flag_name, None) is not True:
            _fail(f"governance_impact_views.{flag_name} must be True")

    for flag_name in VIEW_REQUIRED_FALSE_FLAGS:
        if getattr(governance_impact_views, flag_name, None) is not False:
            _fail(f"governance_impact_views.{flag_name} must be False")


def _validate_index_behavior() -> None:
    receipts = (
        {
            "execution_id": "execution-001",
            "governance_traceability": [
                {"type": "ADR", "id": "ADR-0016"},
                {"type": "RULE", "id": "RULE-016-4"},
            ],
        },
        {
            "execution_id": "execution-002",
            "governance_traceability": [
                {"type": "ADR", "id": "ADR-0016"},
            ],
        },
    )

    index = impact_index.build_impact_index(receipts)

    impacted = index.impacted_executions("ADR-0016")
    if impacted != ("execution-001", "execution-002"):
        _fail("ImpactIndex impacted execution result mismatch")

    payload = index.canonical_dict_for_governance("ADR-0016")

    if payload["runtime_authority"] is not False:
        _fail("ImpactIndex payload runtime authority must remain false")

    if payload["validation_authority"] is not False:
        _fail("ImpactIndex payload validation authority must remain false")

    if payload["governance_authority"] is not False:
        _fail("ImpactIndex payload governance authority must remain false")


def _validate_query_behavior() -> None:
    receipts = (
        {
            "execution_id": "execution-001",
            "governance_traceability": [
                {"type": "ADR", "id": "ADR-0018"},
            ],
        },
    )

    payload = impact_query.query_impact_payload("ADR-0018", receipts)

    if payload["impacted_executions"] != ["execution-001"]:
        _fail("Impact query payload impacted execution mismatch")

    if payload["runtime_authority"] is not False:
        _fail("Impact query runtime authority must remain false")

    if payload["governance_authority"] is not False:
        _fail("Impact query governance authority must remain false")

    if payload["decision_authority"] is not False:
        _fail("Impact query decision authority must remain false")


def _validate_view_behavior() -> None:
    receipts = (
        {
            "execution_id": "execution-001",
            "governance_traceability": [
                {"type": "ADR", "id": "ADR-0016"},
            ],
        },
    )

    payload = governance_impact_views.build_governance_impact_response(
        governance_id="ADR-0016",
        receipts=receipts,
    )

    if payload["api_status"] != "READ_ONLY_GOVERNANCE_IMPACT_API":
        _fail("Governance impact API status mismatch")

    if payload["impacted_executions"] != ["execution-001"]:
        _fail("Governance impact API impacted execution mismatch")

    if payload["runtime_authority"] is not False:
        _fail("Governance impact API runtime authority must remain false")

    if payload["validation_authority"] is not False:
        _fail("Governance impact API validation authority must remain false")

    if payload["governance_authority"] is not False:
        _fail("Governance impact API governance authority must remain false")


def validate_governance_impact() -> None:
    """Validate the Governance Impact Query boundary."""

    _validate_index_flags()
    _validate_query_flags()
    _validate_view_flags()

    for module in VALIDATED_MODULES:
        _validate_forbidden_imports(module)
        _validate_forbidden_calls(module)
        _validate_forbidden_mutation_attributes(module)

    _validate_index_behavior()
    _validate_query_behavior()
    _validate_view_behavior()


def main() -> None:
    try:
        validate_governance_impact()
    except GovernanceImpactValidationError as exc:
        print(f"Governance impact validation FAILED: {exc}")
        sys.exit(1)

    print("Governance impact validation PASSED")


if __name__ == "__main__":
    main()