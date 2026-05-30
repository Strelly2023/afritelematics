"""
AFRIPower enterprise intelligence graph projection.

This module projects execution, governance, proof, traceability, and
explainability references into a read-only enterprise intelligence view.

Constitutional boundary:
- consumes authority
- does not create authority
- does not execute runtime behavior
- does not validate runtime truth
- does not enforce governance
- does not mutate receipts or proof artifacts
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from afritech.afripower.constants import (
    AFRIPOWER_PROJECTION_STATUS,
    ALLOWED_EDGE_TYPES,
    ALLOWED_NODE_TYPES,
    DISPLAY_ONLY,
    ENTERPRISE_INTELLIGENCE_ONLY,
    GOVERNANCE_AUTHORITY,
    GRAPH_DATA_CLASSIFICATION,
    GRAPH_OUTPUT_CLASSIFICATION,
    GRAPH_RELATIONSHIP_CLASSIFICATION,
    LAW_AFRIPOWER_CANNOT_CREATE_AUTHORITY_SURFACE,
    LAW_AFRIPOWER_CANNOT_INFLUENCE_CI,
    LAW_AFRIPOWER_CANNOT_INFLUENCE_GOVERNANCE,
    LAW_AFRIPOWER_CANNOT_INFLUENCE_PROOF,
    LAW_AFRIPOWER_CANNOT_INFLUENCE_REPLAY,
    LAW_AFRIPOWER_CANNOT_INFLUENCE_RUNTIME,
    LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    LAW_AFRIPOWER_IS_DISPLAY_ONLY,
    LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
    LAW_AFRIPOWER_IS_READ_ONLY,
    PROJECTION_CREATES_AUTHORITY,
    PROJECTION_ONLY,
    READ_ONLY,
    REFERENCE_ONLY,
    RUNTIME_AUTHORITY,
    VALIDATION_AUTHORITY,
)


@dataclass(frozen=True)
class AFRIPowerNode:
    """Immutable read-only AFRIPower graph node."""

    node_type: str
    node_id: str
    label: str | None = None

    def __post_init__(self) -> None:
        if self.node_type not in ALLOWED_NODE_TYPES:
            raise ValueError(f"unsupported AFRIPower node type: {self.node_type}")
        if not self.node_id:
            raise ValueError("AFRIPower node id is required")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "type": self.node_type,
            "id": self.node_id,
            "label": self.label or self.node_id,
            "projection_status": AFRIPOWER_PROJECTION_STATUS,
            "data_classification": GRAPH_DATA_CLASSIFICATION,
            "output_classification": GRAPH_OUTPUT_CLASSIFICATION,
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "reference_only": REFERENCE_ONLY,
            "projection_only": PROJECTION_ONLY,
            "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,
            "non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
            "runtime_authority": RUNTIME_AUTHORITY,
            "validation_authority": VALIDATION_AUTHORITY,
            "governance_authority": GOVERNANCE_AUTHORITY,
        }


@dataclass(frozen=True)
class AFRIPowerEdge:
    """Immutable read-only AFRIPower graph edge."""

    source_id: str
    target_id: str
    relation: str

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("AFRIPower edge source_id is required")
        if not self.target_id:
            raise ValueError("AFRIPower edge target_id is required")
        if self.relation not in ALLOWED_EDGE_TYPES:
            raise ValueError(f"unsupported AFRIPower edge relation: {self.relation}")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "projection_status": AFRIPOWER_PROJECTION_STATUS,
            "relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,
            "data_classification": GRAPH_DATA_CLASSIFICATION,
            "output_classification": GRAPH_OUTPUT_CLASSIFICATION,
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "reference_only": REFERENCE_ONLY,
            "projection_only": PROJECTION_ONLY,
            "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,
            "non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
            "creates_authority": PROJECTION_CREATES_AUTHORITY,
            "influences_runtime": not LAW_AFRIPOWER_CANNOT_INFLUENCE_RUNTIME,
            "influences_replay": not LAW_AFRIPOWER_CANNOT_INFLUENCE_REPLAY,
            "influences_proof": not LAW_AFRIPOWER_CANNOT_INFLUENCE_PROOF,
            "influences_ci": not LAW_AFRIPOWER_CANNOT_INFLUENCE_CI,
            "influences_governance": not LAW_AFRIPOWER_CANNOT_INFLUENCE_GOVERNANCE,
        }


@dataclass(frozen=True)
class AFRIPowerKnowledgeGraph:
    """Immutable read-only AFRIPower enterprise intelligence graph."""

    nodes: tuple[AFRIPowerNode, ...]
    edges: tuple[AFRIPowerEdge, ...]

    def canonical_dict(self) -> dict[str, object]:
        return {
            "projection_status": AFRIPOWER_PROJECTION_STATUS,
            "data_classification": GRAPH_DATA_CLASSIFICATION,
            "output_classification": GRAPH_OUTPUT_CLASSIFICATION,
            "relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "reference_only": REFERENCE_ONLY,
            "projection_only": PROJECTION_ONLY,
            "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,
            "non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
            "consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
            "creates_authority": PROJECTION_CREATES_AUTHORITY,
            "cannot_create_authority": LAW_AFRIPOWER_CANNOT_CREATE_AUTHORITY_SURFACE,
            "influences_runtime": not LAW_AFRIPOWER_CANNOT_INFLUENCE_RUNTIME,
            "influences_replay": not LAW_AFRIPOWER_CANNOT_INFLUENCE_REPLAY,
            "influences_proof": not LAW_AFRIPOWER_CANNOT_INFLUENCE_PROOF,
            "influences_ci": not LAW_AFRIPOWER_CANNOT_INFLUENCE_CI,
            "influences_governance": not LAW_AFRIPOWER_CANNOT_INFLUENCE_GOVERNANCE,
            "runtime_authority": RUNTIME_AUTHORITY,
            "validation_authority": VALIDATION_AUTHORITY,
            "governance_authority": GOVERNANCE_AUTHORITY,
            "nodes": [node.canonical_dict() for node in self.nodes],
            "edges": [edge.canonical_dict() for edge in self.edges],
        }


def _safe_str(value: object, fallback: str = "") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _normalize_node_type(value: object) -> str:
    normalized = _safe_str(value).upper()

    mappings = {
        "ENTERPRISE": "Enterprise",
        "CAPABILITY": "Capability",
        "WORKFLOW": "Workflow",
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BIND": "Binding",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
        "EXPLAINABILITY": "Explanation",
    }

    return mappings.get(normalized, _safe_str(value, "Execution"))


def _extract_traceability_references(
    payload: Mapping[str, object],
) -> tuple[dict[str, str], ...]:
    raw_refs = payload.get("traceability", payload.get("governance_traceability", []))

    if isinstance(raw_refs, (str, bytes)) or not isinstance(raw_refs, Iterable):
        return tuple()

    references: list[dict[str, str]] = []

    for raw_ref in raw_refs:
        if not isinstance(raw_ref, Mapping):
            continue

        ref_type = _safe_str(raw_ref.get("type"))
        ref_id = _safe_str(raw_ref.get("id"))

        if not ref_type or not ref_id:
            continue

        references.append(
            {
                "type": _normalize_node_type(ref_type),
                "id": ref_id,
            }
        )

    return tuple(references)


def build_afripower_knowledge_graph(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:
    """Build a deterministic read-only AFRIPower enterprise intelligence graph."""

    nodes: list[AFRIPowerNode] = []
    edges: list[AFRIPowerEdge] = []
    seen_nodes: set[tuple[str, str]] = set()
    seen_edges: set[tuple[str, str, str]] = set()

    def add_node(node_type: str, node_id: str, label: str | None = None) -> None:
        normalized_type = _normalize_node_type(node_type)
        key = (normalized_type, node_id)

        if key in seen_nodes:
            return

        nodes.append(
            AFRIPowerNode(
                node_type=normalized_type,
                node_id=node_id,
                label=label or node_id,
            )
        )
        seen_nodes.add(key)

    def add_edge(source_id: str, target_id: str, relation: str) -> None:
        key = (source_id, target_id, relation)

        if key in seen_edges:
            return

        edges.append(
            AFRIPowerEdge(
                source_id=source_id,
                target_id=target_id,
                relation=relation,
            )
        )
        seen_edges.add(key)

    for payload in payloads:
        execution_id = _safe_str(payload.get("execution_id"), "unknown-execution")
        add_node("Execution", execution_id)

        for reference in _extract_traceability_references(payload):
            ref_type = reference["type"]
            ref_id = reference["id"]

            add_node(ref_type, ref_id)
            add_edge(execution_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(
        nodes=tuple(nodes),
        edges=tuple(edges),
    )


def build_afripower_knowledge_graph_dict(
    payloads: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    return build_afripower_knowledge_graph(payloads).canonical_dict()


def build_graph_projection(
    payloads: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    """Compatibility helper for AFRIPower graph projection."""

    return build_afripower_knowledge_graph_dict(payloads)


__all__ = [
    "AFRIPowerNode",
    "AFRIPowerEdge",
    "AFRIPowerKnowledgeGraph",
    "build_afripower_knowledge_graph",
    "build_afripower_knowledge_graph_dict",
    "build_graph_projection",
]
