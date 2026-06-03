"""
AFRIPower graph projection service.

This module converts receipt/proof/trace references into a read-only
enterprise intelligence graph.

It does not:
- validate truth
- execute runtime behavior
- mutate artifacts
- create authority
- influence replay/proof/CI/governance
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from afritech.afripower.contracts.read_only_contract import (
    assert_read_only_contract,
)
from afritech.afripower.graph.constants import (
    GRAPH_DATA_CLASSIFICATION,
    GRAPH_DISPLAY_ONLY,
    GRAPH_ENTERPRISE_INTELLIGENCE_ONLY,
    GRAPH_OUTPUT_CLASSIFICATION,
    GRAPH_PROJECTION_ONLY,
    GRAPH_READ_ONLY,
    GRAPH_REFERENCE_ONLY,
    GRAPH_RELATIONSHIP_CLASSIFICATION,
    assert_graph_constants,
)
from afritech.afripower.graph.models import (
    AFRIPowerGraph,
    AFRIPowerGraphEdge,
    AFRIPowerGraphModelError,
    AFRIPowerGraphNode,
)

#afritech/afripower/graph/projection.py

class AFRIPowerGraphProjectionError(RuntimeError):
    """Raised when graph projection fails."""


@dataclass(frozen=True)
class AFRIPowerProjectionInput:
    """Read-only projection input wrapper."""

    artifact_id: str
    artifact_type: str
    label: str | None = None
    references: tuple[tuple[str, str], ...] = tuple()

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise AFRIPowerGraphProjectionError(
                "projection artifact_id is required"
            )

        if not self.artifact_type:
            raise AFRIPowerGraphProjectionError(
                "projection artifact_type is required"
            )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "label": self.label or self.artifact_id,
            "references": [
                {
                    "type": ref_type,
                    "id": ref_id,
                }
                for ref_type, ref_id in self.references
            ],
            "read_only": GRAPH_READ_ONLY,
            "reference_only": GRAPH_REFERENCE_ONLY,
            "display_only": GRAPH_DISPLAY_ONLY,
            "projection_only": GRAPH_PROJECTION_ONLY,
            "enterprise_intelligence_only": (
                GRAPH_ENTERPRISE_INTELLIGENCE_ONLY
            ),
            "creates_authority": False,
            "validates_truth": False,
            "executes_runtime": False,
            "mutates_artifacts": False,
        }


def _safe_str(value: object, fallback: str = "") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback

def _normalize_artifact_type(value: object) -> str:
    normalized = _safe_str(value).upper()

    mappings = {
        "ENTERPRISE": "Enterprise",
        "CAPABILITY": "Capability",
        "WORKFLOW": "Workflow",
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "BIND": "Binding",
        "RECEIPT": "Receipt",
        "RECEIPT_REFERENCE": "Receipt",
        "PROOF": "Proof",
        "PROOF_REFERENCE": "Proof",
        "TRACE": "Traceability",
        "TRACEABILITY": "Traceability",
        "TRACEABILITY_REFERENCE": "Traceability",
        "EXPLANATION": "Explanation",
        "DASHBOARD": "Dashboard",
        "METRIC": "Metric",
        "INSIGHT": "Insight",
    }

    return mappings.get(normalized, _safe_str(value, "Execution"))

def _extract_reference_pairs(
    payload: Mapping[str, object],
) -> tuple[tuple[str, str], ...]:
    #raw_refs = payload.get("references", payload.get("traceability", []))
    
    raw_refs = payload.get(
    "references",
    payload.get(
        "traceability",
        payload.get("governance_traceability", []),
    ),
)
    if isinstance(raw_refs, (str, bytes)) or not isinstance(raw_refs, Iterable):
        return tuple()

    refs: list[tuple[str, str]] = []

    for raw_ref in raw_refs:
        if not isinstance(raw_ref, Mapping):
            continue

        raw_ref_type = raw_ref.get("type") or raw_ref.get("artifact_type")

        raw_ref_id = raw_ref.get("id") or raw_ref.get("artifact_id")


        if not raw_ref_type or not raw_ref_id:
                 continue
        
        ref_type = _normalize_artifact_type(raw_ref_type)
        ref_id = _safe_str(raw_ref_id)

        if not ref_id:
            continue

        refs.append((ref_type, ref_id))

    return tuple(refs)


def projection_input_from_mapping(
    payload: Mapping[str, object],
) -> AFRIPowerProjectionInput:
    """Create a read-only projection input from a mapping."""

    if not isinstance(payload, Mapping):
        raise AFRIPowerGraphProjectionError(
            "projection payload must be a mapping"
        )

    artifact_id = _safe_str(
        payload.get("artifact_id")
        or payload.get("execution_id")
        or payload.get("receipt_id")
        or payload.get("proof_id")
        or payload.get("id")
    )

    artifact_type = _normalize_artifact_type(
        payload.get("artifact_type")
        or payload.get("receipt_type")
        or payload.get("proof_type")
        or payload.get("type")
        or "Execution"
    )

    label = _safe_str(payload.get("label"), artifact_id) or None
    references = _extract_reference_pairs(payload)

    return AFRIPowerProjectionInput(
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        label=label,
        references=references,
    )


def build_graph_from_projection_inputs(
    inputs: Iterable[AFRIPowerProjectionInput],
) -> AFRIPowerGraph:
    """Build an immutable read-only AFRIPower graph."""

    assert_read_only_contract()
    assert_graph_constants()

    nodes: list[AFRIPowerGraphNode] = []
    edges: list[AFRIPowerGraphEdge] = []
    seen_nodes: set[tuple[str, str]] = set()
    seen_edges: set[tuple[str, str, str]] = set()

    def add_node(
        *,
        node_id: str,
        node_type: str,
        label: str | None = None,
    ) -> None:
        key = (node_type, node_id)

        if key in seen_nodes:
            return

        nodes.append(
            AFRIPowerGraphNode(
                node_id=node_id,
                node_type=node_type,
                label=label or node_id,
            )
        )
        seen_nodes.add(key)

    def add_edge(
        *,
        source_id: str,
        target_id: str,
        relation: str,
    ) -> None:
        key = (source_id, target_id, relation)

        if key in seen_edges:
            return

        edges.append(
            AFRIPowerGraphEdge(
                source_id=source_id,
                target_id=target_id,
                relation=relation,
            )
        )
        seen_edges.add(key)

    for item in inputs:
        add_node(
            node_id=item.artifact_id,
            node_type=item.artifact_type,
            label=item.label,
        )

        for ref_type, ref_id in item.references:
            add_node(
                node_id=ref_id,
                node_type=ref_type,
                label=ref_id,
            )
            add_edge(
                source_id=item.artifact_id,
                target_id=ref_id,
                relation="references",
            )

    try:
        return AFRIPowerGraph(
            nodes=tuple(nodes),
            edges=tuple(edges),
        )
    except AFRIPowerGraphModelError as exc:
        raise AFRIPowerGraphProjectionError(str(exc)) from exc


def build_graph_projection_from_mappings(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerGraph:
    """Build an AFRIPower graph from mapping payloads."""

    inputs = tuple(
        projection_input_from_mapping(payload)
        for payload in payloads
    )

    return build_graph_from_projection_inputs(inputs)


def build_graph_projection_dict_from_mappings(
    payloads: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    graph = build_graph_projection_from_mappings(payloads)
    data = graph.canonical_dict()

    data.update(
        {
            "projection_service": "afritech.afripower.graph.projection",
            "data_classification": GRAPH_DATA_CLASSIFICATION,
            "output_classification": GRAPH_OUTPUT_CLASSIFICATION,
            "relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,
            "read_only": GRAPH_READ_ONLY,
            "reference_only": GRAPH_REFERENCE_ONLY,
            "display_only": GRAPH_DISPLAY_ONLY,
            "projection_only": GRAPH_PROJECTION_ONLY,
            "enterprise_intelligence_only": (
                GRAPH_ENTERPRISE_INTELLIGENCE_ONLY
            ),
            "creates_authority": False,
            "validates_truth": False,
            "executes_runtime": False,
            "mutates_artifacts": False,
        }
    )

    return data




# Compatibility aliases
build_projection_graph = build_graph_projection_from_mappings
build_projection_graph_dict = build_graph_projection_dict_from_mappings


def project_graph(
    payloads: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    """Legacy compatibility alias for read-only graph projection."""

    data = build_graph_projection_dict_from_mappings(payloads)

    data.update(
        {
            "authoritative": False,
            "observational_only": True,
            "graph_status": "OBSERVATIONAL_ONLY",
        }
    )

    return data




__all__ = [
    "AFRIPowerGraphProjectionError",
    "AFRIPowerProjectionInput",
    "projection_input_from_mapping",
    "build_graph_from_projection_inputs",
    "build_graph_projection_from_mappings",
    "build_graph_projection_dict_from_mappings",
    "build_projection_graph",
    "build_projection_graph_dict",
    "project_graph",

]
