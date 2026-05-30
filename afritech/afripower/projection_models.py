"""
Read-only AFRIPower projection models.

These models represent enterprise intelligence projection data only.

Constitutional boundary:
- read-only
- reference-only
- display-only
- non-authoritative
- no runtime authority
- no replay authority
- no proof authority
- no CI authority
- no governance authority
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

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
class AFRIPowerProjectionNode:
    """Immutable read-only AFRIPower projection node."""

    node_type: str
    node_id: str
    label: str | None = None

    def __post_init__(self) -> None:
        if self.node_type not in ALLOWED_NODE_TYPES:
            raise ValueError(
                f"unsupported AFRIPower projection node type: {self.node_type}"
            )
        if not self.node_id:
            raise ValueError("AFRIPower projection node id is required")

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
class AFRIPowerProjectionEdge:
    """Immutable read-only AFRIPower projection edge."""

    source_id: str
    target_id: str
    relation: str

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("AFRIPower projection edge source_id is required")
        if not self.target_id:
            raise ValueError("AFRIPower projection edge target_id is required")
        if self.relation not in ALLOWED_EDGE_TYPES:
            raise ValueError(
                f"unsupported AFRIPower projection edge relation: {self.relation}"
            )

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
class AFRIPowerProjection:
    """Immutable read-only AFRIPower enterprise intelligence projection."""

    nodes: tuple[AFRIPowerProjectionNode, ...]
    edges: tuple[AFRIPowerProjectionEdge, ...]

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
            "cannot_create_authority": (
                LAW_AFRIPOWER_CANNOT_CREATE_AUTHORITY_SURFACE
            ),
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


def normalize_node_type(value: object) -> str:
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


def extract_traceability_references(
    payload: Mapping[str, object],
) -> tuple[dict[str, str], ...]:
    raw_refs = payload.get("traceability", [])

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
                "type": normalize_node_type(ref_type),
                "id": ref_id,
            }
        )

    return tuple(references)


def build_afripower_projection(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerProjection:
    """Build a deterministic read-only AFRIPower projection."""

    nodes: list[AFRIPowerProjectionNode] = []
    edges: list[AFRIPowerProjectionEdge] = []
    seen_nodes: set[tuple[str, str]] = set()
    seen_edges: set[tuple[str, str, str]] = set()

    def add_node(node_type: str, node_id: str, label: str | None = None) -> None:
        normalized_type = normalize_node_type(node_type)
        key = (normalized_type, node_id)

        if key in seen_nodes:
            return

        nodes.append(
            AFRIPowerProjectionNode(
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
            AFRIPowerProjectionEdge(
                source_id=source_id,
                target_id=target_id,
                relation=relation,
            )
        )
        seen_edges.add(key)

    for payload in payloads:
        execution_id = _safe_str(
            payload.get("execution_id"),
            "unknown-execution",
        )

        add_node("Execution", execution_id)

        for reference in extract_traceability_references(payload):
            ref_type = reference["type"]
            ref_id = reference["id"]

            add_node(ref_type, ref_id)
            add_edge(execution_id, ref_id, "references")

    return AFRIPowerProjection(
        nodes=tuple(nodes),
        edges=tuple(edges),
    )


def build_projection_node(
    node_type: str,
    node_id: str,
    label: str | None = None,
) -> AFRIPowerProjectionNode:
    return AFRIPowerProjectionNode(
        node_type=normalize_node_type(node_type),
        node_id=node_id,
        label=label,
    )


def projection_node_to_dict(
    node: AFRIPowerProjectionNode,
) -> dict[str, object]:
    return node.canonical_dict()


def build_projection_edge(
    source_id: str,
    target_id: str,
    relation: str,
) -> AFRIPowerProjectionEdge:
    return AFRIPowerProjectionEdge(
        source_id=source_id,
        target_id=target_id,
        relation=relation,
    )


def projection_edge_to_dict(
    edge: AFRIPowerProjectionEdge,
) -> dict[str, object]:
    return edge.canonical_dict()


def build_afripower_projection_dict(
    payloads: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    return build_afripower_projection(payloads).canonical_dict()


__all__ = [
    "AFRIPowerProjectionNode",
    "AFRIPowerProjectionEdge",
    "AFRIPowerProjection",
    "normalize_node_type",
    "extract_traceability_references",
    "build_projection_node",
    "projection_node_to_dict",
    "build_projection_edge",
    "projection_edge_to_dict",
    "build_afripower_projection",
    "build_afripower_projection_dict",
]
