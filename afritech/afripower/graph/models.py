"""
AFRIPower graph models.

These models represent read-only enterprise intelligence graph data.

They are projection models only.

They must not:
- execute runtime behavior
- validate runtime truth
- mutate receipts
- mutate proof artifacts
- create authority
- influence governance
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from afritech.afripower.graph.constants import (
    GRAPH_COMPONENT,
    GRAPH_DATA_CLASSIFICATION,
    GRAPH_DISPLAY_ONLY,
    GRAPH_EDGE_TYPES,
    GRAPH_ENTERPRISE_INTELLIGENCE_ONLY,
    GRAPH_NODE_TYPES,
    GRAPH_OUTPUT_CLASSIFICATION,
    GRAPH_PROJECTION_ONLY,
    GRAPH_READ_ONLY,
    GRAPH_REFERENCE_ONLY,
    GRAPH_RELATIONSHIP_CLASSIFICATION,
)


class AFRIPowerGraphModelError(ValueError):
    """Raised when AFRIPower graph model data is invalid."""


def _safe_str(value: object, fallback: str = "") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _freeze_metadata(
    metadata: Mapping[str, object] | None,
) -> tuple[tuple[str, object], ...]:
    if metadata is None:
        return tuple()

    if not isinstance(metadata, Mapping):
        raise AFRIPowerGraphModelError("metadata must be a mapping")

    return tuple(sorted(metadata.items(), key=lambda item: str(item[0])))


@dataclass(frozen=True)
class AFRIPowerGraphNode:
    """Immutable read-only graph node."""

    node_id: str
    node_type: str
    label: str | None = None
    metadata: tuple[tuple[str, object], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.node_id:
            raise AFRIPowerGraphModelError("graph node_id is required")

        if self.node_type not in GRAPH_NODE_TYPES:
            raise AFRIPowerGraphModelError(
                f"unsupported graph node_type: {self.node_type}"
            )

        object.__setattr__(
            self,
            "metadata",
            _freeze_metadata(dict(self.metadata)),
        )

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, object],
    ) -> "AFRIPowerGraphNode":
        if not isinstance(payload, Mapping):
            raise AFRIPowerGraphModelError("node payload must be a mapping")

        node_id = _safe_str(payload.get("node_id") or payload.get("id"))
        node_type = _safe_str(payload.get("node_type") or payload.get("type"))
        label = _safe_str(payload.get("label"), node_id) or None

        raw_metadata = payload.get("metadata", {})
        if not isinstance(raw_metadata, Mapping):
            raise AFRIPowerGraphModelError("node metadata must be a mapping")

        return cls(
            node_id=node_id,
            node_type=node_type,
            label=label,
            metadata=_freeze_metadata(raw_metadata),
        )

    def metadata_dict(self) -> dict[str, object]:
        return dict(self.metadata)

    def canonical_dict(self) -> dict[str, object]:
        return {
            "component": GRAPH_COMPONENT,
            "node_id": self.node_id,
            "node_type": self.node_type,
            "label": self.label or self.node_id,
            "metadata": self.metadata_dict(),
            "data_classification": GRAPH_DATA_CLASSIFICATION,
            "output_classification": GRAPH_OUTPUT_CLASSIFICATION,
            "read_only": GRAPH_READ_ONLY,
            "reference_only": GRAPH_REFERENCE_ONLY,
            "display_only": GRAPH_DISPLAY_ONLY,
            "projection_only": GRAPH_PROJECTION_ONLY,
            "enterprise_intelligence_only": GRAPH_ENTERPRISE_INTELLIGENCE_ONLY,
            "creates_authority": False,
            "validates_truth": False,
            "executes_runtime": False,
            "mutates_artifacts": False,
        }


@dataclass(frozen=True)
class AFRIPowerGraphEdge:
    """Immutable read-only graph edge."""

    source_id: str
    target_id: str
    relation: str
    metadata: tuple[tuple[str, object], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.source_id:
            raise AFRIPowerGraphModelError("graph edge source_id is required")

        if not self.target_id:
            raise AFRIPowerGraphModelError("graph edge target_id is required")

        if self.relation not in GRAPH_EDGE_TYPES:
            raise AFRIPowerGraphModelError(
                f"unsupported graph edge relation: {self.relation}"
            )

        object.__setattr__(
            self,
            "metadata",
            _freeze_metadata(dict(self.metadata)),
        )

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, object],
    ) -> "AFRIPowerGraphEdge":
        if not isinstance(payload, Mapping):
            raise AFRIPowerGraphModelError("edge payload must be a mapping")

        source_id = _safe_str(payload.get("source_id"))
        target_id = _safe_str(payload.get("target_id"))
        relation = _safe_str(payload.get("relation"))

        raw_metadata = payload.get("metadata", {})
        if not isinstance(raw_metadata, Mapping):
            raise AFRIPowerGraphModelError("edge metadata must be a mapping")

        return cls(
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            metadata=_freeze_metadata(raw_metadata),
        )

    def metadata_dict(self) -> dict[str, object]:
        return dict(self.metadata)

    def canonical_dict(self) -> dict[str, object]:
        return {
            "component": GRAPH_COMPONENT,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "metadata": self.metadata_dict(),
            "relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,
            "data_classification": GRAPH_DATA_CLASSIFICATION,
            "output_classification": GRAPH_OUTPUT_CLASSIFICATION,
            "read_only": GRAPH_READ_ONLY,
            "reference_only": GRAPH_REFERENCE_ONLY,
            "display_only": GRAPH_DISPLAY_ONLY,
            "projection_only": GRAPH_PROJECTION_ONLY,
            "enterprise_intelligence_only": GRAPH_ENTERPRISE_INTELLIGENCE_ONLY,
            "creates_authority": False,
            "validates_truth": False,
            "executes_runtime": False,
            "mutates_artifacts": False,
            "influences_runtime": False,
            "influences_replay": False,
            "influences_proof": False,
            "influences_ci": False,
            "influences_governance": False,
        }


@dataclass(frozen=True)
class AFRIPowerGraph:
    """Immutable read-only AFRIPower graph."""

    nodes: tuple[AFRIPowerGraphNode, ...]
    edges: tuple[AFRIPowerGraphEdge, ...]

    def __post_init__(self) -> None:
        node_ids = {node.node_id for node in self.nodes}

        for edge in self.edges:
            if edge.source_id not in node_ids:
                raise AFRIPowerGraphModelError(
                    f"edge source missing from graph nodes: {edge.source_id}"
                )

            if edge.target_id not in node_ids:
                raise AFRIPowerGraphModelError(
                    f"edge target missing from graph nodes: {edge.target_id}"
                )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "component": GRAPH_COMPONENT,
            "data_classification": GRAPH_DATA_CLASSIFICATION,
            "output_classification": GRAPH_OUTPUT_CLASSIFICATION,
            "relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,
            "read_only": GRAPH_READ_ONLY,
            "reference_only": GRAPH_REFERENCE_ONLY,
            "display_only": GRAPH_DISPLAY_ONLY,
            "projection_only": GRAPH_PROJECTION_ONLY,
            "enterprise_intelligence_only": GRAPH_ENTERPRISE_INTELLIGENCE_ONLY,
            "creates_authority": False,
            "validates_truth": False,
            "executes_runtime": False,
            "mutates_artifacts": False,
            "nodes": [node.canonical_dict() for node in self.nodes],
            "edges": [edge.canonical_dict() for edge in self.edges],
        }


def build_graph_from_mappings(
    *,
    nodes: tuple[Mapping[str, object], ...],
    edges: tuple[Mapping[str, object], ...],
) -> AFRIPowerGraph:
    """Build a read-only graph from mapping payloads."""

    graph_nodes = tuple(
        AFRIPowerGraphNode.from_mapping(node)
        for node in nodes
    )
    graph_edges = tuple(
        AFRIPowerGraphEdge.from_mapping(edge)
        for edge in edges
    )

    return AFRIPowerGraph(
        nodes=graph_nodes,
        edges=graph_edges,
    )


def build_graph_dict_from_mappings(
    *,
    nodes: tuple[Mapping[str, object], ...],
    edges: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    return build_graph_from_mappings(
        nodes=nodes,
        edges=edges,
    ).canonical_dict()


__all__ = [
    "AFRIPowerGraphModelError",
    "AFRIPowerGraphNode",
    "AFRIPowerGraphEdge",
    "AFRIPowerGraph",
    "build_graph_from_mappings",
    "build_graph_dict_from_mappings",
]
