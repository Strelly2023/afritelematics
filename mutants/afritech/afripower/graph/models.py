"""
AFRIPower Graph Models

Read-only, representation-only graph models.

This module MUST NEVER:
- execute runtime behavior
- validate truth
- enforce governance
- mutate receipts
- mutate proof artifacts
- create authority
- determine admissibility

Graph nodes are representations.
Graph edges are relationships.
Neither nodes nor edges are authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Any, Dict, Tuple, List, Set
from copy import deepcopy

from afritech.afripower.graph.constants import (
    DISPLAY_ONLY,
    GRAPH_CLASSIFICATION,
    GRAPH_STATUS,
    OBSERVATIONAL_ONLY,
    READ_ONLY,
    REPRESENTATION_ONLY,
    ALLOWED_NODE_TYPES,
    ALLOWED_EDGE_TYPES,
)
from typing import Annotated
from typing import Callable
from typing import ClassVar

MutantDict = Annotated[dict[str, Callable], "Mutant"] # type: ignore


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None): # type: ignore
    """Forward call to original or mutated function, depending on the environment"""
    import os # type: ignore
    mutant_under_test = os.environ['MUTANT_UNDER_TEST'] # type: ignore
    if mutant_under_test == 'fail': # type: ignore
        from mutmut.__main__ import MutmutProgrammaticFailException # type: ignore
        raise MutmutProgrammaticFailException('Failed programmatically')       # type: ignore
    elif mutant_under_test == 'stats': # type: ignore
        from mutmut.__main__ import record_trampoline_hit # type: ignore
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__) # type: ignore
        # (for class methods, orig is bound and thus does not need the explicit self argument)
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_' # type: ignore
    if not mutant_under_test.startswith(prefix): # type: ignore
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    mutant_name = mutant_under_test.rpartition('.')[-1] # type: ignore
    if self_arg is not None: # type: ignore
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs) # type: ignore
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs) # type: ignore
    return result # type: ignore

# =============================================================================
# SAFE HELPERS
# =============================================================================


def _safe_str(value: object) -> str:
    args = [value]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__safe_str__mutmut_orig, x__safe_str__mutmut_mutants, args, kwargs, None)

# =============================================================================
# SAFE HELPERS
# =============================================================================


def x__safe_str__mutmut_orig(value: object) -> str:
    if isinstance(value, str):
        value = value.strip()
        if value:
            return value
    return ""

# =============================================================================
# SAFE HELPERS
# =============================================================================


def x__safe_str__mutmut_1(value: object) -> str:
    if isinstance(value, str):
        value = None
        if value:
            return value
    return ""

# =============================================================================
# SAFE HELPERS
# =============================================================================


def x__safe_str__mutmut_2(value: object) -> str:
    if isinstance(value, str):
        value = value.strip()
        if value:
            return value
    return "XXXX"

x__safe_str__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__safe_str__mutmut_1': x__safe_str__mutmut_1, 
    'x__safe_str__mutmut_2': x__safe_str__mutmut_2
}
x__safe_str__mutmut_orig.__name__ = 'x__safe_str'


def _safe_mapping(value: object) -> Dict[str, Any]:
    args = [value]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__safe_mapping__mutmut_orig, x__safe_mapping__mutmut_mutants, args, kwargs, None)


def x__safe_mapping__mutmut_orig(value: object) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def x__safe_mapping__mutmut_1(value: object) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(None)
    return {}

x__safe_mapping__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__safe_mapping__mutmut_1': x__safe_mapping__mutmut_1
}
x__safe_mapping__mutmut_orig.__name__ = 'x__safe_mapping'


# =============================================================================
# NODE MODEL
# =============================================================================


@dataclass(frozen=True)
class GraphNode:
    """
    Immutable representation-only graph node.

    ✅ Validated type
    ✅ Deep immutable metadata
    """

    id: str
    type: str
    label: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        node_type = _safe_str(self.type)
        node_id = _safe_str(self.id)

        if not node_id:
            raise ValueError("GraphNode id is required")

        if node_type not in ALLOWED_NODE_TYPES:
            raise ValueError(f"unsupported graph node type: {node_type}")

        object.__setattr__(self, "type", node_type)
        object.__setattr__(self, "id", node_id)
        object.__setattr__(self, "metadata", deepcopy(_safe_mapping(self.metadata)))

    def canonical_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label or self.id,
            "metadata": deepcopy(dict(self.metadata)),

            # graph metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            # authority guarantee
            "authoritative": False,
        }


# =============================================================================
# EDGE MODEL
# =============================================================================


@dataclass(frozen=True)
class GraphEdge:
    """
    Immutable representation-only graph edge.

    ✅ Validated relation
    ✅ Deep immutable metadata
    """

    source_id: str
    target_id: str
    relation: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        source_id = _safe_str(self.source_id)
        target_id = _safe_str(self.target_id)
        relation = _safe_str(self.relation)

        if not source_id or not target_id:
            raise ValueError("GraphEdge requires source_id and target_id")

        if relation not in ALLOWED_EDGE_TYPES:
            raise ValueError(f"unsupported graph relation: {relation}")

        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "target_id", target_id)
        object.__setattr__(self, "relation", relation)
        object.__setattr__(self, "metadata", deepcopy(_safe_mapping(self.metadata)))

    def canonical_dict(self) -> Dict[str, object]:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "relation": self.relation,
            "metadata": deepcopy(dict(self.metadata)),

            # graph metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            # authority guarantee
            "authoritative": False,
        }


# =============================================================================
# GRAPH PROJECTION MODEL
# =============================================================================


@dataclass(frozen=True)
class GraphProjection:
    """
    Immutable representation-only graph projection.

    ✅ Deduplicated
    ✅ Deterministic
    ✅ Non-authoritative
    """

    nodes: Tuple[GraphNode, ...] = ()
    edges: Tuple[GraphEdge, ...] = ()

    def canonical_dict(self) -> Dict[str, object]:
        return {
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,

            # data
            "nodes": [n.canonical_dict() for n in self.nodes],
            "edges": [e.canonical_dict() for e in self.edges],
        }


# =============================================================================
# BUILDERS
# =============================================================================


def build_graph_node(
    node_id: str,
    node_type: str,
    label: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> GraphNode:
    args = [node_id, node_type, label, metadata]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_graph_node__mutmut_orig, x_build_graph_node__mutmut_mutants, args, kwargs, None)


# =============================================================================
# BUILDERS
# =============================================================================


def x_build_graph_node__mutmut_orig(
    node_id: str,
    node_type: str,
    label: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> GraphNode:
    """Build validated graph node."""

    return GraphNode(
        id=node_id,
        type=node_type,
        label=label,
        metadata=_safe_mapping(metadata or {}),
    )


# =============================================================================
# BUILDERS
# =============================================================================


def x_build_graph_node__mutmut_1(
    node_id: str,
    node_type: str,
    label: str = "XXXX",
    metadata: Mapping[str, Any] | None = None,
) -> GraphNode:
    """Build validated graph node."""

    return GraphNode(
        id=node_id,
        type=node_type,
        label=label,
        metadata=_safe_mapping(metadata or {}),
    )


# =============================================================================
# BUILDERS
# =============================================================================


def x_build_graph_node__mutmut_2(
    node_id: str,
    node_type: str,
    label: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> GraphNode:
    """Build validated graph node."""

    return GraphNode(
        id=None,
        type=node_type,
        label=label,
        metadata=_safe_mapping(metadata or {}),
    )


# =============================================================================
# BUILDERS
# =============================================================================


def x_build_graph_node__mutmut_3(
    node_id: str,
    node_type: str,
    label: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> GraphNode:
    """Build validated graph node."""

    return GraphNode(
        id=node_id,
        type=None,
        label=label,
        metadata=_safe_mapping(metadata or {}),
    )


# =============================================================================
# BUILDERS
# =============================================================================


def x_build_graph_node__mutmut_4(
    node_id: str,
    node_type: str,
    label: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> GraphNode:
    """Build validated graph node."""

    return GraphNode(
        id=node_id,
        type=node_type,
        label=None,
        metadata=_safe_mapping(metadata or {}),
    )


# =============================================================================
# BUILDERS
# =============================================================================


def x_build_graph_node__mutmut_5(
    node_id: str,
    node_type: str,
    label: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> GraphNode:
    """Build validated graph node."""

    return GraphNode(
        id=node_id,
        type=node_type,
        label=label,
        metadata=None,
    )


# =============================================================================
# BUILDERS
# =============================================================================


def x_build_graph_node__mutmut_6(
    node_id: str,
    node_type: str,
    label: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> GraphNode:
    """Build validated graph node."""

    return GraphNode(
        type=node_type,
        label=label,
        metadata=_safe_mapping(metadata or {}),
    )


# =============================================================================
# BUILDERS
# =============================================================================


def x_build_graph_node__mutmut_7(
    node_id: str,
    node_type: str,
    label: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> GraphNode:
    """Build validated graph node."""

    return GraphNode(
        id=node_id,
        label=label,
        metadata=_safe_mapping(metadata or {}),
    )


# =============================================================================
# BUILDERS
# =============================================================================


def x_build_graph_node__mutmut_8(
    node_id: str,
    node_type: str,
    label: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> GraphNode:
    """Build validated graph node."""

    return GraphNode(
        id=node_id,
        type=node_type,
        metadata=_safe_mapping(metadata or {}),
    )


# =============================================================================
# BUILDERS
# =============================================================================


def x_build_graph_node__mutmut_9(
    node_id: str,
    node_type: str,
    label: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> GraphNode:
    """Build validated graph node."""

    return GraphNode(
        id=node_id,
        type=node_type,
        label=label,
        )


# =============================================================================
# BUILDERS
# =============================================================================


def x_build_graph_node__mutmut_10(
    node_id: str,
    node_type: str,
    label: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> GraphNode:
    """Build validated graph node."""

    return GraphNode(
        id=node_id,
        type=node_type,
        label=label,
        metadata=_safe_mapping(None),
    )


# =============================================================================
# BUILDERS
# =============================================================================


def x_build_graph_node__mutmut_11(
    node_id: str,
    node_type: str,
    label: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> GraphNode:
    """Build validated graph node."""

    return GraphNode(
        id=node_id,
        type=node_type,
        label=label,
        metadata=_safe_mapping(metadata and {}),
    )

x_build_graph_node__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_graph_node__mutmut_1': x_build_graph_node__mutmut_1, 
    'x_build_graph_node__mutmut_2': x_build_graph_node__mutmut_2, 
    'x_build_graph_node__mutmut_3': x_build_graph_node__mutmut_3, 
    'x_build_graph_node__mutmut_4': x_build_graph_node__mutmut_4, 
    'x_build_graph_node__mutmut_5': x_build_graph_node__mutmut_5, 
    'x_build_graph_node__mutmut_6': x_build_graph_node__mutmut_6, 
    'x_build_graph_node__mutmut_7': x_build_graph_node__mutmut_7, 
    'x_build_graph_node__mutmut_8': x_build_graph_node__mutmut_8, 
    'x_build_graph_node__mutmut_9': x_build_graph_node__mutmut_9, 
    'x_build_graph_node__mutmut_10': x_build_graph_node__mutmut_10, 
    'x_build_graph_node__mutmut_11': x_build_graph_node__mutmut_11
}
x_build_graph_node__mutmut_orig.__name__ = 'x_build_graph_node'


def build_graph_edge(
    source_id: str,
    target_id: str,
    relation: str,
    metadata: Mapping[str, Any] | None = None,
) -> GraphEdge:
    args = [source_id, target_id, relation, metadata]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_graph_edge__mutmut_orig, x_build_graph_edge__mutmut_mutants, args, kwargs, None)


def x_build_graph_edge__mutmut_orig(
    source_id: str,
    target_id: str,
    relation: str,
    metadata: Mapping[str, Any] | None = None,
) -> GraphEdge:
    """Build validated graph edge."""

    return GraphEdge(
        source_id=source_id,
        target_id=target_id,
        relation=relation,
        metadata=_safe_mapping(metadata or {}),
    )


def x_build_graph_edge__mutmut_1(
    source_id: str,
    target_id: str,
    relation: str,
    metadata: Mapping[str, Any] | None = None,
) -> GraphEdge:
    """Build validated graph edge."""

    return GraphEdge(
        source_id=None,
        target_id=target_id,
        relation=relation,
        metadata=_safe_mapping(metadata or {}),
    )


def x_build_graph_edge__mutmut_2(
    source_id: str,
    target_id: str,
    relation: str,
    metadata: Mapping[str, Any] | None = None,
) -> GraphEdge:
    """Build validated graph edge."""

    return GraphEdge(
        source_id=source_id,
        target_id=None,
        relation=relation,
        metadata=_safe_mapping(metadata or {}),
    )


def x_build_graph_edge__mutmut_3(
    source_id: str,
    target_id: str,
    relation: str,
    metadata: Mapping[str, Any] | None = None,
) -> GraphEdge:
    """Build validated graph edge."""

    return GraphEdge(
        source_id=source_id,
        target_id=target_id,
        relation=None,
        metadata=_safe_mapping(metadata or {}),
    )


def x_build_graph_edge__mutmut_4(
    source_id: str,
    target_id: str,
    relation: str,
    metadata: Mapping[str, Any] | None = None,
) -> GraphEdge:
    """Build validated graph edge."""

    return GraphEdge(
        source_id=source_id,
        target_id=target_id,
        relation=relation,
        metadata=None,
    )


def x_build_graph_edge__mutmut_5(
    source_id: str,
    target_id: str,
    relation: str,
    metadata: Mapping[str, Any] | None = None,
) -> GraphEdge:
    """Build validated graph edge."""

    return GraphEdge(
        target_id=target_id,
        relation=relation,
        metadata=_safe_mapping(metadata or {}),
    )


def x_build_graph_edge__mutmut_6(
    source_id: str,
    target_id: str,
    relation: str,
    metadata: Mapping[str, Any] | None = None,
) -> GraphEdge:
    """Build validated graph edge."""

    return GraphEdge(
        source_id=source_id,
        relation=relation,
        metadata=_safe_mapping(metadata or {}),
    )


def x_build_graph_edge__mutmut_7(
    source_id: str,
    target_id: str,
    relation: str,
    metadata: Mapping[str, Any] | None = None,
) -> GraphEdge:
    """Build validated graph edge."""

    return GraphEdge(
        source_id=source_id,
        target_id=target_id,
        metadata=_safe_mapping(metadata or {}),
    )


def x_build_graph_edge__mutmut_8(
    source_id: str,
    target_id: str,
    relation: str,
    metadata: Mapping[str, Any] | None = None,
) -> GraphEdge:
    """Build validated graph edge."""

    return GraphEdge(
        source_id=source_id,
        target_id=target_id,
        relation=relation,
        )


def x_build_graph_edge__mutmut_9(
    source_id: str,
    target_id: str,
    relation: str,
    metadata: Mapping[str, Any] | None = None,
) -> GraphEdge:
    """Build validated graph edge."""

    return GraphEdge(
        source_id=source_id,
        target_id=target_id,
        relation=relation,
        metadata=_safe_mapping(None),
    )


def x_build_graph_edge__mutmut_10(
    source_id: str,
    target_id: str,
    relation: str,
    metadata: Mapping[str, Any] | None = None,
) -> GraphEdge:
    """Build validated graph edge."""

    return GraphEdge(
        source_id=source_id,
        target_id=target_id,
        relation=relation,
        metadata=_safe_mapping(metadata and {}),
    )

x_build_graph_edge__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_graph_edge__mutmut_1': x_build_graph_edge__mutmut_1, 
    'x_build_graph_edge__mutmut_2': x_build_graph_edge__mutmut_2, 
    'x_build_graph_edge__mutmut_3': x_build_graph_edge__mutmut_3, 
    'x_build_graph_edge__mutmut_4': x_build_graph_edge__mutmut_4, 
    'x_build_graph_edge__mutmut_5': x_build_graph_edge__mutmut_5, 
    'x_build_graph_edge__mutmut_6': x_build_graph_edge__mutmut_6, 
    'x_build_graph_edge__mutmut_7': x_build_graph_edge__mutmut_7, 
    'x_build_graph_edge__mutmut_8': x_build_graph_edge__mutmut_8, 
    'x_build_graph_edge__mutmut_9': x_build_graph_edge__mutmut_9, 
    'x_build_graph_edge__mutmut_10': x_build_graph_edge__mutmut_10
}
x_build_graph_edge__mutmut_orig.__name__ = 'x_build_graph_edge'


def build_graph_projection(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    args = [nodes, edges]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_graph_projection__mutmut_orig, x_build_graph_projection__mutmut_mutants, args, kwargs, None)


def x_build_graph_projection__mutmut_orig(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_1(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = None
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_2(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = None

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_3(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = None
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_4(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = None

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_5(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_6(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            break
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_7(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = None
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_8(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_9(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(None)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_10(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(None)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_11(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_12(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            break
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_13(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = None
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_14(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_15(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(None)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_16(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(None)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_17(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=None,
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_18(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=None,
    )


def x_build_graph_projection__mutmut_19(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_20(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        )


def x_build_graph_projection__mutmut_21(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(None),
        edges=tuple(unique_edges),
    )


def x_build_graph_projection__mutmut_22(
    nodes: Iterable[GraphNode] = (),
    edges: Iterable[GraphEdge] = (),
) -> GraphProjection:
    """
    Build deduplicated graph projection.

    ✅ Deterministic
    ✅ Safe
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[GraphNode] = []
    unique_edges: List[GraphEdge] = []

    for n in nodes:
        if not isinstance(n, GraphNode):
            continue
        key = (n.type, n.id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        if not isinstance(e, GraphEdge):
            continue
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return GraphProjection(
        nodes=tuple(unique_nodes),
        edges=tuple(None),
    )

x_build_graph_projection__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_graph_projection__mutmut_1': x_build_graph_projection__mutmut_1, 
    'x_build_graph_projection__mutmut_2': x_build_graph_projection__mutmut_2, 
    'x_build_graph_projection__mutmut_3': x_build_graph_projection__mutmut_3, 
    'x_build_graph_projection__mutmut_4': x_build_graph_projection__mutmut_4, 
    'x_build_graph_projection__mutmut_5': x_build_graph_projection__mutmut_5, 
    'x_build_graph_projection__mutmut_6': x_build_graph_projection__mutmut_6, 
    'x_build_graph_projection__mutmut_7': x_build_graph_projection__mutmut_7, 
    'x_build_graph_projection__mutmut_8': x_build_graph_projection__mutmut_8, 
    'x_build_graph_projection__mutmut_9': x_build_graph_projection__mutmut_9, 
    'x_build_graph_projection__mutmut_10': x_build_graph_projection__mutmut_10, 
    'x_build_graph_projection__mutmut_11': x_build_graph_projection__mutmut_11, 
    'x_build_graph_projection__mutmut_12': x_build_graph_projection__mutmut_12, 
    'x_build_graph_projection__mutmut_13': x_build_graph_projection__mutmut_13, 
    'x_build_graph_projection__mutmut_14': x_build_graph_projection__mutmut_14, 
    'x_build_graph_projection__mutmut_15': x_build_graph_projection__mutmut_15, 
    'x_build_graph_projection__mutmut_16': x_build_graph_projection__mutmut_16, 
    'x_build_graph_projection__mutmut_17': x_build_graph_projection__mutmut_17, 
    'x_build_graph_projection__mutmut_18': x_build_graph_projection__mutmut_18, 
    'x_build_graph_projection__mutmut_19': x_build_graph_projection__mutmut_19, 
    'x_build_graph_projection__mutmut_20': x_build_graph_projection__mutmut_20, 
    'x_build_graph_projection__mutmut_21': x_build_graph_projection__mutmut_21, 
    'x_build_graph_projection__mutmut_22': x_build_graph_projection__mutmut_22
}
x_build_graph_projection__mutmut_orig.__name__ = 'x_build_graph_projection'


# =============================================================================
# SERIALIZATION HELPERS
# =============================================================================


def graph_projection_to_dict(graph: GraphProjection) -> Dict[str, object]:
    """Serialize projection safely."""

    return graph.canonical_dict()


# =============================================================================
# INTEGRITY CHECK (CI USE)
# =============================================================================


def assert_graph_models_integrity() -> None:
    args = []# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_assert_graph_models_integrity__mutmut_orig, x_assert_graph_models_integrity__mutmut_mutants, args, kwargs, None)


# =============================================================================
# INTEGRITY CHECK (CI USE)
# =============================================================================


def x_assert_graph_models_integrity__mutmut_orig() -> None:
    """
    Validate structural integrity.

    Raises:
        RuntimeError if invariants are violated.
    """

    if not READ_ONLY:
        raise RuntimeError("Graph must remain read-only")

    if not REPRESENTATION_ONLY:
        raise RuntimeError("Graph must remain representation-only")


# =============================================================================
# INTEGRITY CHECK (CI USE)
# =============================================================================


def x_assert_graph_models_integrity__mutmut_1() -> None:
    """
    Validate structural integrity.

    Raises:
        RuntimeError if invariants are violated.
    """

    if READ_ONLY:
        raise RuntimeError("Graph must remain read-only")

    if not REPRESENTATION_ONLY:
        raise RuntimeError("Graph must remain representation-only")


# =============================================================================
# INTEGRITY CHECK (CI USE)
# =============================================================================


def x_assert_graph_models_integrity__mutmut_2() -> None:
    """
    Validate structural integrity.

    Raises:
        RuntimeError if invariants are violated.
    """

    if not READ_ONLY:
        raise RuntimeError(None)

    if not REPRESENTATION_ONLY:
        raise RuntimeError("Graph must remain representation-only")


# =============================================================================
# INTEGRITY CHECK (CI USE)
# =============================================================================


def x_assert_graph_models_integrity__mutmut_3() -> None:
    """
    Validate structural integrity.

    Raises:
        RuntimeError if invariants are violated.
    """

    if not READ_ONLY:
        raise RuntimeError("XXGraph must remain read-onlyXX")

    if not REPRESENTATION_ONLY:
        raise RuntimeError("Graph must remain representation-only")


# =============================================================================
# INTEGRITY CHECK (CI USE)
# =============================================================================


def x_assert_graph_models_integrity__mutmut_4() -> None:
    """
    Validate structural integrity.

    Raises:
        RuntimeError if invariants are violated.
    """

    if not READ_ONLY:
        raise RuntimeError("graph must remain read-only")

    if not REPRESENTATION_ONLY:
        raise RuntimeError("Graph must remain representation-only")


# =============================================================================
# INTEGRITY CHECK (CI USE)
# =============================================================================


def x_assert_graph_models_integrity__mutmut_5() -> None:
    """
    Validate structural integrity.

    Raises:
        RuntimeError if invariants are violated.
    """

    if not READ_ONLY:
        raise RuntimeError("GRAPH MUST REMAIN READ-ONLY")

    if not REPRESENTATION_ONLY:
        raise RuntimeError("Graph must remain representation-only")


# =============================================================================
# INTEGRITY CHECK (CI USE)
# =============================================================================


def x_assert_graph_models_integrity__mutmut_6() -> None:
    """
    Validate structural integrity.

    Raises:
        RuntimeError if invariants are violated.
    """

    if not READ_ONLY:
        raise RuntimeError("Graph must remain read-only")

    if REPRESENTATION_ONLY:
        raise RuntimeError("Graph must remain representation-only")


# =============================================================================
# INTEGRITY CHECK (CI USE)
# =============================================================================


def x_assert_graph_models_integrity__mutmut_7() -> None:
    """
    Validate structural integrity.

    Raises:
        RuntimeError if invariants are violated.
    """

    if not READ_ONLY:
        raise RuntimeError("Graph must remain read-only")

    if not REPRESENTATION_ONLY:
        raise RuntimeError(None)


# =============================================================================
# INTEGRITY CHECK (CI USE)
# =============================================================================


def x_assert_graph_models_integrity__mutmut_8() -> None:
    """
    Validate structural integrity.

    Raises:
        RuntimeError if invariants are violated.
    """

    if not READ_ONLY:
        raise RuntimeError("Graph must remain read-only")

    if not REPRESENTATION_ONLY:
        raise RuntimeError("XXGraph must remain representation-onlyXX")


# =============================================================================
# INTEGRITY CHECK (CI USE)
# =============================================================================


def x_assert_graph_models_integrity__mutmut_9() -> None:
    """
    Validate structural integrity.

    Raises:
        RuntimeError if invariants are violated.
    """

    if not READ_ONLY:
        raise RuntimeError("Graph must remain read-only")

    if not REPRESENTATION_ONLY:
        raise RuntimeError("graph must remain representation-only")


# =============================================================================
# INTEGRITY CHECK (CI USE)
# =============================================================================


def x_assert_graph_models_integrity__mutmut_10() -> None:
    """
    Validate structural integrity.

    Raises:
        RuntimeError if invariants are violated.
    """

    if not READ_ONLY:
        raise RuntimeError("Graph must remain read-only")

    if not REPRESENTATION_ONLY:
        raise RuntimeError("GRAPH MUST REMAIN REPRESENTATION-ONLY")

x_assert_graph_models_integrity__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_assert_graph_models_integrity__mutmut_1': x_assert_graph_models_integrity__mutmut_1, 
    'x_assert_graph_models_integrity__mutmut_2': x_assert_graph_models_integrity__mutmut_2, 
    'x_assert_graph_models_integrity__mutmut_3': x_assert_graph_models_integrity__mutmut_3, 
    'x_assert_graph_models_integrity__mutmut_4': x_assert_graph_models_integrity__mutmut_4, 
    'x_assert_graph_models_integrity__mutmut_5': x_assert_graph_models_integrity__mutmut_5, 
    'x_assert_graph_models_integrity__mutmut_6': x_assert_graph_models_integrity__mutmut_6, 
    'x_assert_graph_models_integrity__mutmut_7': x_assert_graph_models_integrity__mutmut_7, 
    'x_assert_graph_models_integrity__mutmut_8': x_assert_graph_models_integrity__mutmut_8, 
    'x_assert_graph_models_integrity__mutmut_9': x_assert_graph_models_integrity__mutmut_9, 
    'x_assert_graph_models_integrity__mutmut_10': x_assert_graph_models_integrity__mutmut_10
}
x_assert_graph_models_integrity__mutmut_orig.__name__ = 'x_assert_graph_models_integrity'


# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    "GraphNode",
    "GraphEdge",
    "GraphProjection",
    "build_graph_node",
    "build_graph_edge",
    "build_graph_projection",
    "graph_projection_to_dict",
    "assert_graph_models_integrity",
]