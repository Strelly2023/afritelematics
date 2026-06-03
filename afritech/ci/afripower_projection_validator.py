"""
CI validator for AFRIPower enterprise intelligence projection.

Constitutional Law
------------------
AFRIPower consumes authority.
AFRIPower does not create authority.

AFRIPower projection may organize and display references from doctrine,
governance, execution, proof, traceability, and explainability.

It must not:
- execute runtime behavior
- validate runtime truth
- enforce governance
- mutate receipts
- mutate proof artifacts
- load YAML
- access DB state
- import runtime/proof/registry/governance authority modules
- create runtime, replay, proof, CI, admissibility, or governance authority
"""

from __future__ import annotations

import ast
import inspect
import sys
from types import ModuleType

from afritech.afripower import constants, graph_projection, projection_models


class AFRIPowerProjectionValidationError(RuntimeError):
    """Raised when AFRIPower projection violates constitutional law."""


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
    "DECISION_AUTHORITY",
    "ADMISSIBILITY_AUTHORITY",
    "MUTATION_ALLOWED",
    "RECEIPT_MUTATION_ALLOWED",
    "PROOF_MUTATION_ALLOWED",
    "GOVERNANCE_MUTATION_ALLOWED",
    "RUNTIME_DEPENDENCY",
    "PROJECTION_CREATES_AUTHORITY",
)

REQUIRED_TRUE_FLAGS = (
    "REFERENCE_ONLY",
    "READ_ONLY",
    "DISPLAY_ONLY",
    "PROJECTION_ONLY",
    "ENTERPRISE_INTELLIGENCE_ONLY",
    "INVARIANT_AFRIPOWER_IS_READ_ONLY",
    "INVARIANT_AFRIPOWER_IS_NON_AUTHORITATIVE",
    "INVARIANT_AFRIPOWER_IS_DISPLAY_ONLY",
    "INVARIANT_AFRIPOWER_CONSUMES_AUTHORITY_ONLY",
    "INVARIANT_AFRIPOWER_CANNOT_CREATE_AUTHORITY",
    "INVARIANT_AFRIPOWER_CANNOT_INFLUENCE_RUNTIME",
    "INVARIANT_AFRIPOWER_CANNOT_INFLUENCE_REPLAY",
    "INVARIANT_AFRIPOWER_CANNOT_INFLUENCE_PROOF",
    "INVARIANT_AFRIPOWER_CANNOT_INFLUENCE_CI",
    "INVARIANT_AFRIPOWER_CANNOT_INFLUENCE_GOVERNANCE",
)

VALIDATED_MODULES = (
    constants,
    graph_projection,
    projection_models,
)


def _fail(message: str) -> None:
    raise AFRIPowerProjectionValidationError(message)


def _source(module: ModuleType) -> str:
    return inspect.getsource(module)


def _tree(module: ModuleType) -> ast.Module:
    return ast.parse(_source(module))


def _validate_required_constants() -> None:
    if (
        constants.AFRIPOWER_PROJECTION_STATUS
        != "ENTERPRISE_INTELLIGENCE_PROJECTION"
    ):
        _fail(
            "AFRIPOWER_PROJECTION_STATUS must be "
            "ENTERPRISE_INTELLIGENCE_PROJECTION"
        )

    if constants.GRAPH_DATA_CLASSIFICATION != "REFERENCE_ONLY":
        _fail("GRAPH_DATA_CLASSIFICATION must be REFERENCE_ONLY")

    if (
        constants.GRAPH_OUTPUT_CLASSIFICATION
        != "ENTERPRISE_INTELLIGENCE_VIEW"
    ):
        _fail(
            "GRAPH_OUTPUT_CLASSIFICATION must be "
            "ENTERPRISE_INTELLIGENCE_VIEW"
        )

    if (
        constants.GRAPH_RELATIONSHIP_CLASSIFICATION
        != "NON_AUTHORITATIVE"
    ):
        _fail(
            "GRAPH_RELATIONSHIP_CLASSIFICATION must be "
            "NON_AUTHORITATIVE"
        )

    for flag_name in REQUIRED_FALSE_FLAGS:
        if getattr(constants, flag_name, None) is not False:
            _fail(f"constants.{flag_name} must be False")

    for flag_name in REQUIRED_TRUE_FLAGS:
        if getattr(constants, flag_name, None) is not True:
            _fail(f"constants.{flag_name} must be True")


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


def _validate_projection_models_behavior() -> None:
    node = projection_models.build_projection_node(
        node_type="Execution",
        node_id="execution-001",
    )
    node_payload = projection_models.projection_node_to_dict(node)

    if node_payload["runtime_authority"] is not False:
        _fail("projection node runtime authority must remain false")

    if node_payload["validation_authority"] is not False:
        _fail("projection node validation authority must remain false")

    if node_payload["governance_authority"] is not False:
        _fail("projection node governance authority must remain false")

    edge = projection_models.build_projection_edge(
        source_id="execution-001",
        target_id="ADR-0016",
        relation="references",
    )
    edge_payload = projection_models.projection_edge_to_dict(edge)

    if edge_payload["creates_authority"] is not False:
        _fail("projection edge must not create authority")

    if edge_payload["influences_runtime"] is not False:
        _fail("projection edge must not influence runtime")

    if edge_payload["influences_replay"] is not False:
        _fail("projection edge must not influence replay")

    if edge_payload["influences_proof"] is not False:
        _fail("projection edge must not influence proof")

    if edge_payload["influences_ci"] is not False:
        _fail("projection edge must not influence CI")

    if edge_payload["influences_governance"] is not False:
        _fail("projection edge must not influence governance")

    try:
        projection_models.build_projection_node(
            node_type="Runtime",
            node_id="runtime-001",
        )
    except ValueError:
        pass
    else:
        _fail("projection node accepted unsupported node type")

    try:
        projection_models.build_projection_edge(
            source_id="execution-001",
            target_id="ADR-0016",
            relation="decides",
        )
    except ValueError:
        pass
    else:
        _fail("projection edge accepted unsupported relation")


def _validate_graph_projection_behavior() -> None:
    payloads = (
        {
            "execution_id": "execution-001",
            "governance_traceability": (
                {"type": "ADR", "id": "ADR-0016"},
                {"type": "RULE", "id": "RULE-016-4"},
                {"type": "INVARIANT", "id": "INVARIANT-016"},
            ),
        },
        {
            "execution_id": "execution-002",
            "governance_traceability": (
                {"type": "ADR", "id": "ADR-0016"},
            ),
        },
    )

    graph_payload = graph_projection.build_afripower_knowledge_graph_dict(
        payloads
    )

    if graph_payload["runtime_authority"] is not False:
        _fail("AFRIPower graph runtime authority must remain false")

    if graph_payload["validation_authority"] is not False:
        _fail("AFRIPower graph validation authority must remain false")

    if graph_payload["governance_authority"] is not False:
        _fail("AFRIPower graph governance authority must remain false")

    if graph_payload["creates_authority"] is not False:
        _fail("AFRIPower graph must not create authority")

    if graph_payload["influences_runtime"] is not False:
        _fail("AFRIPower graph must not influence runtime")

    if graph_payload["influences_replay"] is not False:
        _fail("AFRIPower graph must not influence replay")

    if graph_payload["influences_proof"] is not False:
        _fail("AFRIPower graph must not influence proof")

    if graph_payload["influences_ci"] is not False:
        _fail("AFRIPower graph must not influence CI")

    if graph_payload["influences_governance"] is not False:
        _fail("AFRIPower graph must not influence governance")

    if len(graph_payload["nodes"]) != 5:
        _fail("AFRIPower graph node count mismatch")

    if len(graph_payload["edges"]) != 4:
        _fail("AFRIPower graph edge count mismatch")


def validate_afripower_projection() -> None:
    """Validate AFRIPower graph projection boundary."""

    _validate_required_constants()

    for module in VALIDATED_MODULES:
        _validate_forbidden_imports(module)
        _validate_forbidden_calls(module)
        _validate_forbidden_mutation_attributes(module)

    _validate_projection_models_behavior()
    _validate_graph_projection_behavior()


def main() -> None:
    try:
        validate_afripower_projection()
    except AFRIPowerProjectionValidationError as exc:
        print(f"AFRIPower projection validation FAILED: {exc}")
        sys.exit(1)

    print("AFRIPower projection validation PASSED")


if __name__ == "__main__":
    main()