"""
CI validator for the read-only Explainability Graph.

Constitutional Law
------------------
The Explainability Graph may visualize relationships between executions,
governance references, receipts, and proofs.

It must not:
- execute runtime behavior
- validate truth
- enforce governance
- mutate receipts
- load YAML
- access DB state
- influence replay, proof, CI, or runtime authority
"""

from __future__ import annotations

import ast
import inspect
import sys
from types import ModuleType

from afritech.explainability_graph import constants, edge, graph, node


class ExplainabilityGraphValidationError(RuntimeError):
    """Raised when the Explainability Graph violates constitutional law."""


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
    "PROJECTION_DEPENDENCY",
    "PROJECTION_AUTHORITY",
    "RUNTIME_DEPENDENCY",
    "EXECUTION_DEPENDENCY",
    "MUTATION_ALLOWED",
    "STATE_MODIFICATION_ALLOWED",
    "RECEIPT_MUTATION_ALLOWED",
)

REQUIRED_TRUE_FLAGS = (
    "PROJECTION_DISPLAY_ONLY",
    "INVARIANT_GRAPH_IS_READ_ONLY",
    "INVARIANT_GRAPH_IS_NON_AUTHORITATIVE",
    "INVARIANT_GRAPH_IS_DISPLAY_ONLY",
    "INVARIANT_GRAPH_CANNOT_INFLUENCE_RUNTIME",
    "INVARIANT_GRAPH_CANNOT_INFLUENCE_REPLAY",
    "INVARIANT_GRAPH_CANNOT_INFLUENCE_PROOF",
)

VALIDATED_MODULES = (
    constants,
    node,
    edge,
    graph,
)


def _fail(message: str) -> None:
    raise ExplainabilityGraphValidationError(message)


def _source(module: ModuleType) -> str:
    return inspect.getsource(module)


def _tree(module: ModuleType) -> ast.Module:
    return ast.parse(_source(module))


def _validate_required_constants() -> None:
    if constants.GRAPH_STATUS != "READ_ONLY_EXPLAINABILITY_GRAPH":
        _fail("GRAPH_STATUS must be READ_ONLY_EXPLAINABILITY_GRAPH")

    if constants.GRAPH_DATA_CLASSIFICATION != "REFERENCE_ONLY":
        _fail("GRAPH_DATA_CLASSIFICATION must be REFERENCE_ONLY")

    if constants.GRAPH_OUTPUT_CLASSIFICATION != "DISPLAY_ONLY":
        _fail("GRAPH_OUTPUT_CLASSIFICATION must be DISPLAY_ONLY")

    if constants.GRAPH_RELATIONSHIP_CLASSIFICATION != "NON_AUTHORITATIVE":
        _fail(
            "GRAPH_RELATIONSHIP_CLASSIFICATION must be NON_AUTHORITATIVE"
        )

    for flag_name in REQUIRED_FALSE_FLAGS:
        if getattr(constants, flag_name, None) is not False:
            _fail(f"{flag_name} must be False")

    for flag_name in REQUIRED_TRUE_FLAGS:
        if getattr(constants, flag_name, None) is not True:
            _fail(f"{flag_name} must be True")


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
            _fail(
                f"{module.__name__} has forbidden call {call_name}"
            )


def _validate_forbidden_mutation_attributes(module: ModuleType) -> None:
    tree = _tree(module)

    for item in ast.walk(tree):
        if isinstance(item, ast.Attribute):
            if item.attr in FORBIDDEN_MUTATION_ATTRIBUTES:
                _fail(
                    f"{module.__name__} references forbidden mutation "
                    f"attribute {item.attr}"
                )


def _validate_node_behavior() -> None:
    graph_node = node.build_graph_node(
        node_type="Execution",
        node_id="execution-001",
        label="execution-001",
    )

    canonical = graph_node.canonical_dict()

    if canonical["runtime_authority"] is not False:
        _fail("GraphNode runtime authority must remain false")

    if canonical["validation_authority"] is not False:
        _fail("GraphNode validation authority must remain false")

    if canonical["read_only"] is not True:
        _fail("GraphNode must remain read-only")

    if canonical["display_only"] is not True:
        _fail("GraphNode must remain display-only")

    try:
        node.build_graph_node(
            node_type="Runtime",
            node_id="bad-runtime-node",
        )
    except ValueError:
        pass
    else:
        _fail("GraphNode accepted unsupported node type")


def _validate_edge_behavior() -> None:
    graph_edge = edge.build_graph_edge(
        source_id="execution-001",
        target_id="ADR-0016",
        relation="governed_by",
    )

    canonical = graph_edge.canonical_dict()

    if canonical["runtime_authority"] is not False:
        _fail("GraphEdge runtime authority must remain false")

    if canonical["validation_authority"] is not False:
        _fail("GraphEdge validation authority must remain false")

    if canonical["influences_runtime"] is not False:
        _fail("GraphEdge must not influence runtime")

    if canonical["influences_replay"] is not False:
        _fail("GraphEdge must not influence replay")

    if canonical["influences_proof"] is not False:
        _fail("GraphEdge must not influence proof")

    try:
        edge.build_graph_edge(
            source_id="execution-001",
            target_id="ADR-0016",
            relation="decides",
        )
    except ValueError:
        pass
    else:
        _fail("GraphEdge accepted unsupported relation")


def _validate_graph_behavior() -> None:
    payload = {
        "execution_id": "execution-001",
        "governance_traceability": [
            {"type": "ADR", "id": "ADR-0016"},
            {"type": "Invariant", "id": "INVARIANT-016"},
            {"type": "RULE", "id": "RULE-016-4"},
            {"type": "Binding", "id": "BIND-016"},
        ],
    }

    graph_dict = graph.build_explainability_graph_dict(payload)

    if graph_dict["runtime_authority"] is not False:
        _fail("ExplainabilityGraph runtime authority must remain false")

    if graph_dict["validation_authority"] is not False:
        _fail("ExplainabilityGraph validation authority must remain false")

    if graph_dict["influences_runtime"] is not False:
        _fail("ExplainabilityGraph must not influence runtime")

    if graph_dict["influences_replay"] is not False:
        _fail("ExplainabilityGraph must not influence replay")

    if graph_dict["influences_proof"] is not False:
        _fail("ExplainabilityGraph must not influence proof")

    if len(graph_dict["nodes"]) != 5:
        _fail("ExplainabilityGraph node count mismatch")

    if len(graph_dict["edges"]) != 4:
        _fail("ExplainabilityGraph edge count mismatch")

    if "projection_enrichment" in payload:
        _fail("ExplainabilityGraph mutated input payload")


def validate_explainability_graph() -> None:
    """Validate the read-only Explainability Graph boundary."""

    _validate_required_constants()

    for module in VALIDATED_MODULES:
        _validate_forbidden_imports(module)
        _validate_forbidden_calls(module)
        _validate_forbidden_mutation_attributes(module)

    _validate_node_behavior()
    _validate_edge_behavior()
    _validate_graph_behavior()


def main() -> None:
    try:
        validate_explainability_graph()
    except ExplainabilityGraphValidationError as exc:
        print(f"Explainability graph validation FAILED: {exc}")
        sys.exit(1)

    print("Explainability graph validation PASSED")


if __name__ == "__main__":
    main()