"""
Read-only AFRIPower projection models.

These models represent enterprise intelligence projection data only.

ARFIPower projection models are:
    - read-only
    - reference-only
    - display-only

They do NOT:
    - execute runtime behavior
    - validate runtime truth
    - enforce governance
    - mutate receipts / proof
    - create any authority
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple, List, Set

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
# NODE MODEL
# =============================================================================


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

        if not isinstance(self.node_id, str) or not self.node_id.strip():
            raise ValueError("AFRIPower projection node id is required")

    def canonical_dict(self) -> Dict[str, object]:
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


# =============================================================================
# EDGE MODEL
# =============================================================================


@dataclass(frozen=True)
class AFRIPowerProjectionEdge:
    """Immutable read-only AFRIPower projection edge."""

    source_id: str
    target_id: str
    relation: str

    def __post_init__(self) -> None:
        if not self.source_id or not isinstance(self.source_id, str):
            raise ValueError("AFRIPower projection edge source_id is required")

        if not self.target_id or not isinstance(self.target_id, str):
            raise ValueError("AFRIPower projection edge target_id is required")

        if self.relation not in ALLOWED_EDGE_TYPES:
            raise ValueError(
                f"unsupported AFRIPower projection edge relation: {self.relation}"
            )

    def canonical_dict(self) -> Dict[str, object]:
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

            "runtime_authority": RUNTIME_AUTHORITY,
            "validation_authority": VALIDATION_AUTHORITY,
            "governance_authority": GOVERNANCE_AUTHORITY,
            "creates_authority": PROJECTION_CREATES_AUTHORITY,

            "influences_runtime": False,
            "influences_replay": False,
            "influences_proof": False,
            "influences_ci": False,
            "influences_governance": False,
        }


# =============================================================================
# GRAPH MODEL
# =============================================================================


@dataclass(frozen=True)
class AFRIPowerProjectionGraph:
    """Immutable read-only AFRIPower projection graph."""

    nodes: Tuple[AFRIPowerProjectionNode, ...]
    edges: Tuple[AFRIPowerProjectionEdge, ...]

    def canonical_dict(self) -> Dict[str, object]:
        return {
            "projection_status": AFRIPOWER_PROJECTION_STATUS,
            "data_classification": GRAPH_DATA_CLASSIFICATION,
            "output_classification": GRAPH_OUTPUT_CLASSIFICATION,
            "relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

            "read_only": LAW_AFRIPOWER_IS_READ_ONLY,
            "display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
            "reference_only": REFERENCE_ONLY,
            "projection_only": PROJECTION_ONLY,
            "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,
            "non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,

            "consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
            "creates_authority": PROJECTION_CREATES_AUTHORITY,
            "cannot_create_authority": LAW_AFRIPOWER_CANNOT_CREATE_AUTHORITY_SURFACE,

            "runtime_authority": RUNTIME_AUTHORITY,
            "validation_authority": VALIDATION_AUTHORITY,
            "governance_authority": GOVERNANCE_AUTHORITY,

            "influences_runtime": False,
            "influences_replay": False,
            "influences_proof": False,
            "influences_ci": False,
            "influences_governance": False,

            "nodes": [node.canonical_dict() for node in self.nodes],
            "edges": [edge.canonical_dict() for edge in self.edges],
        }


# =============================================================================
# BUILDERS (PURE / SAFE)
# =============================================================================


def _safe_str(value: object) -> str:
    args = [value]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__safe_str__mutmut_orig, x__safe_str__mutmut_mutants, args, kwargs, None)


# =============================================================================
# BUILDERS (PURE / SAFE)
# =============================================================================


def x__safe_str__mutmut_orig(value: object) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


# =============================================================================
# BUILDERS (PURE / SAFE)
# =============================================================================


def x__safe_str__mutmut_1(value: object) -> str:
    return value.strip() if isinstance(value, str) or value.strip() else ""


# =============================================================================
# BUILDERS (PURE / SAFE)
# =============================================================================


def x__safe_str__mutmut_2(value: object) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else "XXXX"

x__safe_str__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__safe_str__mutmut_1': x__safe_str__mutmut_1, 
    'x__safe_str__mutmut_2': x__safe_str__mutmut_2
}
x__safe_str__mutmut_orig.__name__ = 'x__safe_str'


def build_projection_node(node_type: str, node_id: str, label: str | None = None):
    args = [node_type, node_id, label]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_projection_node__mutmut_orig, x_build_projection_node__mutmut_mutants, args, kwargs, None)


def x_build_projection_node__mutmut_orig(node_type: str, node_id: str, label: str | None = None):
    return AFRIPowerProjectionNode(node_type=node_type, node_id=node_id, label=label)


def x_build_projection_node__mutmut_1(node_type: str, node_id: str, label: str | None = None):
    return AFRIPowerProjectionNode(node_type=None, node_id=node_id, label=label)


def x_build_projection_node__mutmut_2(node_type: str, node_id: str, label: str | None = None):
    return AFRIPowerProjectionNode(node_type=node_type, node_id=None, label=label)


def x_build_projection_node__mutmut_3(node_type: str, node_id: str, label: str | None = None):
    return AFRIPowerProjectionNode(node_type=node_type, node_id=node_id, label=None)


def x_build_projection_node__mutmut_4(node_type: str, node_id: str, label: str | None = None):
    return AFRIPowerProjectionNode(node_id=node_id, label=label)


def x_build_projection_node__mutmut_5(node_type: str, node_id: str, label: str | None = None):
    return AFRIPowerProjectionNode(node_type=node_type, label=label)


def x_build_projection_node__mutmut_6(node_type: str, node_id: str, label: str | None = None):
    return AFRIPowerProjectionNode(node_type=node_type, node_id=node_id, )

x_build_projection_node__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_projection_node__mutmut_1': x_build_projection_node__mutmut_1, 
    'x_build_projection_node__mutmut_2': x_build_projection_node__mutmut_2, 
    'x_build_projection_node__mutmut_3': x_build_projection_node__mutmut_3, 
    'x_build_projection_node__mutmut_4': x_build_projection_node__mutmut_4, 
    'x_build_projection_node__mutmut_5': x_build_projection_node__mutmut_5, 
    'x_build_projection_node__mutmut_6': x_build_projection_node__mutmut_6
}
x_build_projection_node__mutmut_orig.__name__ = 'x_build_projection_node'


def build_projection_edge(source_id: str, target_id: str, relation: str):
    args = [source_id, target_id, relation]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_projection_edge__mutmut_orig, x_build_projection_edge__mutmut_mutants, args, kwargs, None)


def x_build_projection_edge__mutmut_orig(source_id: str, target_id: str, relation: str):
    return AFRIPowerProjectionEdge(source_id=source_id, target_id=target_id, relation=relation)


def x_build_projection_edge__mutmut_1(source_id: str, target_id: str, relation: str):
    return AFRIPowerProjectionEdge(source_id=None, target_id=target_id, relation=relation)


def x_build_projection_edge__mutmut_2(source_id: str, target_id: str, relation: str):
    return AFRIPowerProjectionEdge(source_id=source_id, target_id=None, relation=relation)


def x_build_projection_edge__mutmut_3(source_id: str, target_id: str, relation: str):
    return AFRIPowerProjectionEdge(source_id=source_id, target_id=target_id, relation=None)


def x_build_projection_edge__mutmut_4(source_id: str, target_id: str, relation: str):
    return AFRIPowerProjectionEdge(target_id=target_id, relation=relation)


def x_build_projection_edge__mutmut_5(source_id: str, target_id: str, relation: str):
    return AFRIPowerProjectionEdge(source_id=source_id, relation=relation)


def x_build_projection_edge__mutmut_6(source_id: str, target_id: str, relation: str):
    return AFRIPowerProjectionEdge(source_id=source_id, target_id=target_id, )

x_build_projection_edge__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_projection_edge__mutmut_1': x_build_projection_edge__mutmut_1, 
    'x_build_projection_edge__mutmut_2': x_build_projection_edge__mutmut_2, 
    'x_build_projection_edge__mutmut_3': x_build_projection_edge__mutmut_3, 
    'x_build_projection_edge__mutmut_4': x_build_projection_edge__mutmut_4, 
    'x_build_projection_edge__mutmut_5': x_build_projection_edge__mutmut_5, 
    'x_build_projection_edge__mutmut_6': x_build_projection_edge__mutmut_6
}
x_build_projection_edge__mutmut_orig.__name__ = 'x_build_projection_edge'


def build_projection_graph(
    nodes: Tuple[AFRIPowerProjectionNode, ...],
    edges: Tuple[AFRIPowerProjectionEdge, ...],
) -> AFRIPowerProjectionGraph:
    args = [nodes, edges]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_projection_graph__mutmut_orig, x_build_projection_graph__mutmut_mutants, args, kwargs, None)


def x_build_projection_graph__mutmut_orig(
    nodes: Tuple[AFRIPowerProjectionNode, ...],
    edges: Tuple[AFRIPowerProjectionEdge, ...],
) -> AFRIPowerProjectionGraph:
    return AFRIPowerProjectionGraph(nodes=tuple(nodes), edges=tuple(edges))


def x_build_projection_graph__mutmut_1(
    nodes: Tuple[AFRIPowerProjectionNode, ...],
    edges: Tuple[AFRIPowerProjectionEdge, ...],
) -> AFRIPowerProjectionGraph:
    return AFRIPowerProjectionGraph(nodes=None, edges=tuple(edges))


def x_build_projection_graph__mutmut_2(
    nodes: Tuple[AFRIPowerProjectionNode, ...],
    edges: Tuple[AFRIPowerProjectionEdge, ...],
) -> AFRIPowerProjectionGraph:
    return AFRIPowerProjectionGraph(nodes=tuple(nodes), edges=None)


def x_build_projection_graph__mutmut_3(
    nodes: Tuple[AFRIPowerProjectionNode, ...],
    edges: Tuple[AFRIPowerProjectionEdge, ...],
) -> AFRIPowerProjectionGraph:
    return AFRIPowerProjectionGraph(edges=tuple(edges))


def x_build_projection_graph__mutmut_4(
    nodes: Tuple[AFRIPowerProjectionNode, ...],
    edges: Tuple[AFRIPowerProjectionEdge, ...],
) -> AFRIPowerProjectionGraph:
    return AFRIPowerProjectionGraph(nodes=tuple(nodes), )


def x_build_projection_graph__mutmut_5(
    nodes: Tuple[AFRIPowerProjectionNode, ...],
    edges: Tuple[AFRIPowerProjectionEdge, ...],
) -> AFRIPowerProjectionGraph:
    return AFRIPowerProjectionGraph(nodes=tuple(None), edges=tuple(edges))


def x_build_projection_graph__mutmut_6(
    nodes: Tuple[AFRIPowerProjectionNode, ...],
    edges: Tuple[AFRIPowerProjectionEdge, ...],
) -> AFRIPowerProjectionGraph:
    return AFRIPowerProjectionGraph(nodes=tuple(nodes), edges=tuple(None))

x_build_projection_graph__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_projection_graph__mutmut_1': x_build_projection_graph__mutmut_1, 
    'x_build_projection_graph__mutmut_2': x_build_projection_graph__mutmut_2, 
    'x_build_projection_graph__mutmut_3': x_build_projection_graph__mutmut_3, 
    'x_build_projection_graph__mutmut_4': x_build_projection_graph__mutmut_4, 
    'x_build_projection_graph__mutmut_5': x_build_projection_graph__mutmut_5, 
    'x_build_projection_graph__mutmut_6': x_build_projection_graph__mutmut_6
}
x_build_projection_graph__mutmut_orig.__name__ = 'x_build_projection_graph'


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def build_safe_projection_graph(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    args = [nodes, edges]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_safe_projection_graph__mutmut_orig, x_build_safe_projection_graph__mutmut_mutants, args, kwargs, None)


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_orig(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_1(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = None
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_2(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = None

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_3(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = None
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_4(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = None

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_5(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = None
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_6(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_7(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in node_keys:
            node_keys.add(None)
            unique_nodes.append(n)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_8(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(None)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_9(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        key = None
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_10(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_11(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(None)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_12(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(None)

    return AFRIPowerProjectionGraph(
        nodes=tuple(unique_nodes),
        edges=tuple(unique_edges),
    )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_13(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        nodes=None,
        edges=tuple(unique_edges),
    )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_14(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        nodes=tuple(unique_nodes),
        edges=None,
    )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_15(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        edges=tuple(unique_edges),
    )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_16(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        nodes=tuple(unique_nodes),
        )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_17(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        nodes=tuple(None),
        edges=tuple(unique_edges),
    )


# =============================================================================
# DEDUP SAFE GRAPH BUILDER
# =============================================================================


def x_build_safe_projection_graph__mutmut_18(
    nodes: List[AFRIPowerProjectionNode],
    edges: List[AFRIPowerProjectionEdge],
) -> AFRIPowerProjectionGraph:
    """
    Deduplicates nodes and edges deterministically.
    """

    node_keys: Set[Tuple[str, str]] = set()
    edge_keys: Set[Tuple[str, str, str]] = set()

    unique_nodes: List[AFRIPowerProjectionNode] = []
    unique_edges: List[AFRIPowerProjectionEdge] = []

    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in node_keys:
            node_keys.add(key)
            unique_nodes.append(n)

    for e in edges:
        key = (e.source_id, e.target_id, e.relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(e)

    return AFRIPowerProjectionGraph(
        nodes=tuple(unique_nodes),
        edges=tuple(None),
    )

x_build_safe_projection_graph__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_safe_projection_graph__mutmut_1': x_build_safe_projection_graph__mutmut_1, 
    'x_build_safe_projection_graph__mutmut_2': x_build_safe_projection_graph__mutmut_2, 
    'x_build_safe_projection_graph__mutmut_3': x_build_safe_projection_graph__mutmut_3, 
    'x_build_safe_projection_graph__mutmut_4': x_build_safe_projection_graph__mutmut_4, 
    'x_build_safe_projection_graph__mutmut_5': x_build_safe_projection_graph__mutmut_5, 
    'x_build_safe_projection_graph__mutmut_6': x_build_safe_projection_graph__mutmut_6, 
    'x_build_safe_projection_graph__mutmut_7': x_build_safe_projection_graph__mutmut_7, 
    'x_build_safe_projection_graph__mutmut_8': x_build_safe_projection_graph__mutmut_8, 
    'x_build_safe_projection_graph__mutmut_9': x_build_safe_projection_graph__mutmut_9, 
    'x_build_safe_projection_graph__mutmut_10': x_build_safe_projection_graph__mutmut_10, 
    'x_build_safe_projection_graph__mutmut_11': x_build_safe_projection_graph__mutmut_11, 
    'x_build_safe_projection_graph__mutmut_12': x_build_safe_projection_graph__mutmut_12, 
    'x_build_safe_projection_graph__mutmut_13': x_build_safe_projection_graph__mutmut_13, 
    'x_build_safe_projection_graph__mutmut_14': x_build_safe_projection_graph__mutmut_14, 
    'x_build_safe_projection_graph__mutmut_15': x_build_safe_projection_graph__mutmut_15, 
    'x_build_safe_projection_graph__mutmut_16': x_build_safe_projection_graph__mutmut_16, 
    'x_build_safe_projection_graph__mutmut_17': x_build_safe_projection_graph__mutmut_17, 
    'x_build_safe_projection_graph__mutmut_18': x_build_safe_projection_graph__mutmut_18
}
x_build_safe_projection_graph__mutmut_orig.__name__ = 'x_build_safe_projection_graph'


# =============================================================================
# SERIALIZATION HELPERS
# =============================================================================


def projection_node_to_dict(node: AFRIPowerProjectionNode) -> Dict[str, object]:
    return node.canonical_dict()


def projection_edge_to_dict(edge: AFRIPowerProjectionEdge) -> Dict[str, object]:
    return edge.canonical_dict()


def projection_graph_to_dict(graph: AFRIPowerProjectionGraph) -> Dict[str, object]:
    return graph.canonical_dict()