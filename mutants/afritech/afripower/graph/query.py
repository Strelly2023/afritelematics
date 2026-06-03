"""
AFRIPower Graph Query — Read-Only Observation Layer
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any, Dict, Tuple, List

from afritech.afripower.graph.constants import (
    DISPLAY_ONLY,
    GRAPH_CLASSIFICATION,
    GRAPH_STATUS,
    OBSERVATIONAL_ONLY,
    READ_ONLY,
    REPRESENTATION_ONLY,
)

# =============================================================================
# TYPES
# =============================================================================

Graph = Mapping[str, Any]
GraphNode = Mapping[str, Any]
GraphEdge = Mapping[str, Any]
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


def _safe_nodes(graph: Graph) -> Tuple[GraphNode, ...]:
    args = [graph]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__safe_nodes__mutmut_orig, x__safe_nodes__mutmut_mutants, args, kwargs, None)


def x__safe_nodes__mutmut_orig(graph: Graph) -> Tuple[GraphNode, ...]:
    value = graph.get("nodes", ())
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_nodes__mutmut_1(graph: Graph) -> Tuple[GraphNode, ...]:
    value = None
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_nodes__mutmut_2(graph: Graph) -> Tuple[GraphNode, ...]:
    value = graph.get(None, ())
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_nodes__mutmut_3(graph: Graph) -> Tuple[GraphNode, ...]:
    value = graph.get("nodes", None)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_nodes__mutmut_4(graph: Graph) -> Tuple[GraphNode, ...]:
    value = graph.get(())
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_nodes__mutmut_5(graph: Graph) -> Tuple[GraphNode, ...]:
    value = graph.get("nodes", )
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_nodes__mutmut_6(graph: Graph) -> Tuple[GraphNode, ...]:
    value = graph.get("XXnodesXX", ())
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_nodes__mutmut_7(graph: Graph) -> Tuple[GraphNode, ...]:
    value = graph.get("NODES", ())
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_nodes__mutmut_8(graph: Graph) -> Tuple[GraphNode, ...]:
    value = graph.get("nodes", ())
    if not isinstance(value, Sequence) and isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_nodes__mutmut_9(graph: Graph) -> Tuple[GraphNode, ...]:
    value = graph.get("nodes", ())
    if isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_nodes__mutmut_10(graph: Graph) -> Tuple[GraphNode, ...]:
    value = graph.get("nodes", ())
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(None)

x__safe_nodes__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__safe_nodes__mutmut_1': x__safe_nodes__mutmut_1, 
    'x__safe_nodes__mutmut_2': x__safe_nodes__mutmut_2, 
    'x__safe_nodes__mutmut_3': x__safe_nodes__mutmut_3, 
    'x__safe_nodes__mutmut_4': x__safe_nodes__mutmut_4, 
    'x__safe_nodes__mutmut_5': x__safe_nodes__mutmut_5, 
    'x__safe_nodes__mutmut_6': x__safe_nodes__mutmut_6, 
    'x__safe_nodes__mutmut_7': x__safe_nodes__mutmut_7, 
    'x__safe_nodes__mutmut_8': x__safe_nodes__mutmut_8, 
    'x__safe_nodes__mutmut_9': x__safe_nodes__mutmut_9, 
    'x__safe_nodes__mutmut_10': x__safe_nodes__mutmut_10
}
x__safe_nodes__mutmut_orig.__name__ = 'x__safe_nodes'


def _safe_edges(graph: Graph) -> Tuple[GraphEdge, ...]:
    args = [graph]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__safe_edges__mutmut_orig, x__safe_edges__mutmut_mutants, args, kwargs, None)


def x__safe_edges__mutmut_orig(graph: Graph) -> Tuple[GraphEdge, ...]:
    value = graph.get("edges", ())
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_edges__mutmut_1(graph: Graph) -> Tuple[GraphEdge, ...]:
    value = None
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_edges__mutmut_2(graph: Graph) -> Tuple[GraphEdge, ...]:
    value = graph.get(None, ())
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_edges__mutmut_3(graph: Graph) -> Tuple[GraphEdge, ...]:
    value = graph.get("edges", None)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_edges__mutmut_4(graph: Graph) -> Tuple[GraphEdge, ...]:
    value = graph.get(())
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_edges__mutmut_5(graph: Graph) -> Tuple[GraphEdge, ...]:
    value = graph.get("edges", )
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_edges__mutmut_6(graph: Graph) -> Tuple[GraphEdge, ...]:
    value = graph.get("XXedgesXX", ())
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_edges__mutmut_7(graph: Graph) -> Tuple[GraphEdge, ...]:
    value = graph.get("EDGES", ())
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_edges__mutmut_8(graph: Graph) -> Tuple[GraphEdge, ...]:
    value = graph.get("edges", ())
    if not isinstance(value, Sequence) and isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_edges__mutmut_9(graph: Graph) -> Tuple[GraphEdge, ...]:
    value = graph.get("edges", ())
    if isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def x__safe_edges__mutmut_10(graph: Graph) -> Tuple[GraphEdge, ...]:
    value = graph.get("edges", ())
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(None)

x__safe_edges__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__safe_edges__mutmut_1': x__safe_edges__mutmut_1, 
    'x__safe_edges__mutmut_2': x__safe_edges__mutmut_2, 
    'x__safe_edges__mutmut_3': x__safe_edges__mutmut_3, 
    'x__safe_edges__mutmut_4': x__safe_edges__mutmut_4, 
    'x__safe_edges__mutmut_5': x__safe_edges__mutmut_5, 
    'x__safe_edges__mutmut_6': x__safe_edges__mutmut_6, 
    'x__safe_edges__mutmut_7': x__safe_edges__mutmut_7, 
    'x__safe_edges__mutmut_8': x__safe_edges__mutmut_8, 
    'x__safe_edges__mutmut_9': x__safe_edges__mutmut_9, 
    'x__safe_edges__mutmut_10': x__safe_edges__mutmut_10
}
x__safe_edges__mutmut_orig.__name__ = 'x__safe_edges'


# =============================================================================
# BASIC COUNTS
# =============================================================================

def count_nodes(graph: Graph) -> int:
    return len(_safe_nodes(graph))


def count_edges(graph: Graph) -> int:
    return len(_safe_edges(graph))


# =============================================================================
# NODE FILTERS
# =============================================================================

def nodes_by_type(graph: Graph, node_type: str) -> Tuple[Dict[str, object], ...]:
    args = [graph, node_type]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_nodes_by_type__mutmut_orig, x_nodes_by_type__mutmut_mutants, args, kwargs, None)


# =============================================================================
# NODE FILTERS
# =============================================================================

def x_nodes_by_type__mutmut_orig(graph: Graph, node_type: str) -> Tuple[Dict[str, object], ...]:
    t = _safe_str(node_type)

    return tuple(
        dict(n)
        for n in _safe_nodes(graph)
        if _safe_str(n.get("type")) == t
    )


# =============================================================================
# NODE FILTERS
# =============================================================================

def x_nodes_by_type__mutmut_1(graph: Graph, node_type: str) -> Tuple[Dict[str, object], ...]:
    t = None

    return tuple(
        dict(n)
        for n in _safe_nodes(graph)
        if _safe_str(n.get("type")) == t
    )


# =============================================================================
# NODE FILTERS
# =============================================================================

def x_nodes_by_type__mutmut_2(graph: Graph, node_type: str) -> Tuple[Dict[str, object], ...]:
    t = _safe_str(None)

    return tuple(
        dict(n)
        for n in _safe_nodes(graph)
        if _safe_str(n.get("type")) == t
    )


# =============================================================================
# NODE FILTERS
# =============================================================================

def x_nodes_by_type__mutmut_3(graph: Graph, node_type: str) -> Tuple[Dict[str, object], ...]:
    t = _safe_str(node_type)

    return tuple(
        None
    )


# =============================================================================
# NODE FILTERS
# =============================================================================

def x_nodes_by_type__mutmut_4(graph: Graph, node_type: str) -> Tuple[Dict[str, object], ...]:
    t = _safe_str(node_type)

    return tuple(
        dict(None)
        for n in _safe_nodes(graph)
        if _safe_str(n.get("type")) == t
    )


# =============================================================================
# NODE FILTERS
# =============================================================================

def x_nodes_by_type__mutmut_5(graph: Graph, node_type: str) -> Tuple[Dict[str, object], ...]:
    t = _safe_str(node_type)

    return tuple(
        dict(n)
        for n in _safe_nodes(None)
        if _safe_str(n.get("type")) == t
    )


# =============================================================================
# NODE FILTERS
# =============================================================================

def x_nodes_by_type__mutmut_6(graph: Graph, node_type: str) -> Tuple[Dict[str, object], ...]:
    t = _safe_str(node_type)

    return tuple(
        dict(n)
        for n in _safe_nodes(graph)
        if _safe_str(None) == t
    )


# =============================================================================
# NODE FILTERS
# =============================================================================

def x_nodes_by_type__mutmut_7(graph: Graph, node_type: str) -> Tuple[Dict[str, object], ...]:
    t = _safe_str(node_type)

    return tuple(
        dict(n)
        for n in _safe_nodes(graph)
        if _safe_str(n.get(None)) == t
    )


# =============================================================================
# NODE FILTERS
# =============================================================================

def x_nodes_by_type__mutmut_8(graph: Graph, node_type: str) -> Tuple[Dict[str, object], ...]:
    t = _safe_str(node_type)

    return tuple(
        dict(n)
        for n in _safe_nodes(graph)
        if _safe_str(n.get("XXtypeXX")) == t
    )


# =============================================================================
# NODE FILTERS
# =============================================================================

def x_nodes_by_type__mutmut_9(graph: Graph, node_type: str) -> Tuple[Dict[str, object], ...]:
    t = _safe_str(node_type)

    return tuple(
        dict(n)
        for n in _safe_nodes(graph)
        if _safe_str(n.get("TYPE")) == t
    )


# =============================================================================
# NODE FILTERS
# =============================================================================

def x_nodes_by_type__mutmut_10(graph: Graph, node_type: str) -> Tuple[Dict[str, object], ...]:
    t = _safe_str(node_type)

    return tuple(
        dict(n)
        for n in _safe_nodes(graph)
        if _safe_str(n.get("type")) != t
    )

x_nodes_by_type__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_nodes_by_type__mutmut_1': x_nodes_by_type__mutmut_1, 
    'x_nodes_by_type__mutmut_2': x_nodes_by_type__mutmut_2, 
    'x_nodes_by_type__mutmut_3': x_nodes_by_type__mutmut_3, 
    'x_nodes_by_type__mutmut_4': x_nodes_by_type__mutmut_4, 
    'x_nodes_by_type__mutmut_5': x_nodes_by_type__mutmut_5, 
    'x_nodes_by_type__mutmut_6': x_nodes_by_type__mutmut_6, 
    'x_nodes_by_type__mutmut_7': x_nodes_by_type__mutmut_7, 
    'x_nodes_by_type__mutmut_8': x_nodes_by_type__mutmut_8, 
    'x_nodes_by_type__mutmut_9': x_nodes_by_type__mutmut_9, 
    'x_nodes_by_type__mutmut_10': x_nodes_by_type__mutmut_10
}
x_nodes_by_type__mutmut_orig.__name__ = 'x_nodes_by_type'


def execution_nodes(graph: Graph) -> Tuple[Dict[str, object], ...]:
    args = [graph]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_execution_nodes__mutmut_orig, x_execution_nodes__mutmut_mutants, args, kwargs, None)


def x_execution_nodes__mutmut_orig(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return nodes_by_type(graph, "execution")


def x_execution_nodes__mutmut_1(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return nodes_by_type(None, "execution")


def x_execution_nodes__mutmut_2(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return nodes_by_type(graph, None)


def x_execution_nodes__mutmut_3(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return nodes_by_type("execution")


def x_execution_nodes__mutmut_4(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return nodes_by_type(graph, )


def x_execution_nodes__mutmut_5(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return nodes_by_type(graph, "XXexecutionXX")


def x_execution_nodes__mutmut_6(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return nodes_by_type(graph, "EXECUTION")

x_execution_nodes__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_execution_nodes__mutmut_1': x_execution_nodes__mutmut_1, 
    'x_execution_nodes__mutmut_2': x_execution_nodes__mutmut_2, 
    'x_execution_nodes__mutmut_3': x_execution_nodes__mutmut_3, 
    'x_execution_nodes__mutmut_4': x_execution_nodes__mutmut_4, 
    'x_execution_nodes__mutmut_5': x_execution_nodes__mutmut_5, 
    'x_execution_nodes__mutmut_6': x_execution_nodes__mutmut_6
}
x_execution_nodes__mutmut_orig.__name__ = 'x_execution_nodes'


def governance_nodes(graph: Graph) -> Tuple[Dict[str, object], ...]:
    args = [graph]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_governance_nodes__mutmut_orig, x_governance_nodes__mutmut_mutants, args, kwargs, None)


def x_governance_nodes__mutmut_orig(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return tuple(
        dict(n)
        for n in _safe_nodes(graph)
        if _safe_str(n.get("type")) != "execution"
    )


def x_governance_nodes__mutmut_1(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return tuple(
        None
    )


def x_governance_nodes__mutmut_2(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return tuple(
        dict(None)
        for n in _safe_nodes(graph)
        if _safe_str(n.get("type")) != "execution"
    )


def x_governance_nodes__mutmut_3(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return tuple(
        dict(n)
        for n in _safe_nodes(None)
        if _safe_str(n.get("type")) != "execution"
    )


def x_governance_nodes__mutmut_4(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return tuple(
        dict(n)
        for n in _safe_nodes(graph)
        if _safe_str(None) != "execution"
    )


def x_governance_nodes__mutmut_5(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return tuple(
        dict(n)
        for n in _safe_nodes(graph)
        if _safe_str(n.get(None)) != "execution"
    )


def x_governance_nodes__mutmut_6(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return tuple(
        dict(n)
        for n in _safe_nodes(graph)
        if _safe_str(n.get("XXtypeXX")) != "execution"
    )


def x_governance_nodes__mutmut_7(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return tuple(
        dict(n)
        for n in _safe_nodes(graph)
        if _safe_str(n.get("TYPE")) != "execution"
    )


def x_governance_nodes__mutmut_8(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return tuple(
        dict(n)
        for n in _safe_nodes(graph)
        if _safe_str(n.get("type")) == "execution"
    )


def x_governance_nodes__mutmut_9(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return tuple(
        dict(n)
        for n in _safe_nodes(graph)
        if _safe_str(n.get("type")) != "XXexecutionXX"
    )


def x_governance_nodes__mutmut_10(graph: Graph) -> Tuple[Dict[str, object], ...]:
    return tuple(
        dict(n)
        for n in _safe_nodes(graph)
        if _safe_str(n.get("type")) != "EXECUTION"
    )

x_governance_nodes__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_governance_nodes__mutmut_1': x_governance_nodes__mutmut_1, 
    'x_governance_nodes__mutmut_2': x_governance_nodes__mutmut_2, 
    'x_governance_nodes__mutmut_3': x_governance_nodes__mutmut_3, 
    'x_governance_nodes__mutmut_4': x_governance_nodes__mutmut_4, 
    'x_governance_nodes__mutmut_5': x_governance_nodes__mutmut_5, 
    'x_governance_nodes__mutmut_6': x_governance_nodes__mutmut_6, 
    'x_governance_nodes__mutmut_7': x_governance_nodes__mutmut_7, 
    'x_governance_nodes__mutmut_8': x_governance_nodes__mutmut_8, 
    'x_governance_nodes__mutmut_9': x_governance_nodes__mutmut_9, 
    'x_governance_nodes__mutmut_10': x_governance_nodes__mutmut_10
}
x_governance_nodes__mutmut_orig.__name__ = 'x_governance_nodes'


# =============================================================================
# EDGE FILTERS
# =============================================================================

def edges_by_relation(
    graph: Graph,
    relation: str,
) -> Tuple[Dict[str, object], ...]:
    args = [graph, relation]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_edges_by_relation__mutmut_orig, x_edges_by_relation__mutmut_mutants, args, kwargs, None)


# =============================================================================
# EDGE FILTERS
# =============================================================================

def x_edges_by_relation__mutmut_orig(
    graph: Graph,
    relation: str,
) -> Tuple[Dict[str, object], ...]:

    rel = _safe_str(relation)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("relation")) == rel
    )


# =============================================================================
# EDGE FILTERS
# =============================================================================

def x_edges_by_relation__mutmut_1(
    graph: Graph,
    relation: str,
) -> Tuple[Dict[str, object], ...]:

    rel = None

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("relation")) == rel
    )


# =============================================================================
# EDGE FILTERS
# =============================================================================

def x_edges_by_relation__mutmut_2(
    graph: Graph,
    relation: str,
) -> Tuple[Dict[str, object], ...]:

    rel = _safe_str(None)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("relation")) == rel
    )


# =============================================================================
# EDGE FILTERS
# =============================================================================

def x_edges_by_relation__mutmut_3(
    graph: Graph,
    relation: str,
) -> Tuple[Dict[str, object], ...]:

    rel = _safe_str(relation)

    return tuple(
        None
    )


# =============================================================================
# EDGE FILTERS
# =============================================================================

def x_edges_by_relation__mutmut_4(
    graph: Graph,
    relation: str,
) -> Tuple[Dict[str, object], ...]:

    rel = _safe_str(relation)

    return tuple(
        dict(None)
        for e in _safe_edges(graph)
        if _safe_str(e.get("relation")) == rel
    )


# =============================================================================
# EDGE FILTERS
# =============================================================================

def x_edges_by_relation__mutmut_5(
    graph: Graph,
    relation: str,
) -> Tuple[Dict[str, object], ...]:

    rel = _safe_str(relation)

    return tuple(
        dict(e)
        for e in _safe_edges(None)
        if _safe_str(e.get("relation")) == rel
    )


# =============================================================================
# EDGE FILTERS
# =============================================================================

def x_edges_by_relation__mutmut_6(
    graph: Graph,
    relation: str,
) -> Tuple[Dict[str, object], ...]:

    rel = _safe_str(relation)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(None) == rel
    )


# =============================================================================
# EDGE FILTERS
# =============================================================================

def x_edges_by_relation__mutmut_7(
    graph: Graph,
    relation: str,
) -> Tuple[Dict[str, object], ...]:

    rel = _safe_str(relation)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get(None)) == rel
    )


# =============================================================================
# EDGE FILTERS
# =============================================================================

def x_edges_by_relation__mutmut_8(
    graph: Graph,
    relation: str,
) -> Tuple[Dict[str, object], ...]:

    rel = _safe_str(relation)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("XXrelationXX")) == rel
    )


# =============================================================================
# EDGE FILTERS
# =============================================================================

def x_edges_by_relation__mutmut_9(
    graph: Graph,
    relation: str,
) -> Tuple[Dict[str, object], ...]:

    rel = _safe_str(relation)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("RELATION")) == rel
    )


# =============================================================================
# EDGE FILTERS
# =============================================================================

def x_edges_by_relation__mutmut_10(
    graph: Graph,
    relation: str,
) -> Tuple[Dict[str, object], ...]:

    rel = _safe_str(relation)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("relation")) != rel
    )

x_edges_by_relation__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_edges_by_relation__mutmut_1': x_edges_by_relation__mutmut_1, 
    'x_edges_by_relation__mutmut_2': x_edges_by_relation__mutmut_2, 
    'x_edges_by_relation__mutmut_3': x_edges_by_relation__mutmut_3, 
    'x_edges_by_relation__mutmut_4': x_edges_by_relation__mutmut_4, 
    'x_edges_by_relation__mutmut_5': x_edges_by_relation__mutmut_5, 
    'x_edges_by_relation__mutmut_6': x_edges_by_relation__mutmut_6, 
    'x_edges_by_relation__mutmut_7': x_edges_by_relation__mutmut_7, 
    'x_edges_by_relation__mutmut_8': x_edges_by_relation__mutmut_8, 
    'x_edges_by_relation__mutmut_9': x_edges_by_relation__mutmut_9, 
    'x_edges_by_relation__mutmut_10': x_edges_by_relation__mutmut_10
}
x_edges_by_relation__mutmut_orig.__name__ = 'x_edges_by_relation'


def outgoing_edges(
    graph: Graph,
    source_id: str,
) -> Tuple[Dict[str, object], ...]:
    args = [graph, source_id]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_outgoing_edges__mutmut_orig, x_outgoing_edges__mutmut_mutants, args, kwargs, None)


def x_outgoing_edges__mutmut_orig(
    graph: Graph,
    source_id: str,
) -> Tuple[Dict[str, object], ...]:

    src = _safe_str(source_id)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("from")) == src
    )


def x_outgoing_edges__mutmut_1(
    graph: Graph,
    source_id: str,
) -> Tuple[Dict[str, object], ...]:

    src = None

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("from")) == src
    )


def x_outgoing_edges__mutmut_2(
    graph: Graph,
    source_id: str,
) -> Tuple[Dict[str, object], ...]:

    src = _safe_str(None)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("from")) == src
    )


def x_outgoing_edges__mutmut_3(
    graph: Graph,
    source_id: str,
) -> Tuple[Dict[str, object], ...]:

    src = _safe_str(source_id)

    return tuple(
        None
    )


def x_outgoing_edges__mutmut_4(
    graph: Graph,
    source_id: str,
) -> Tuple[Dict[str, object], ...]:

    src = _safe_str(source_id)

    return tuple(
        dict(None)
        for e in _safe_edges(graph)
        if _safe_str(e.get("from")) == src
    )


def x_outgoing_edges__mutmut_5(
    graph: Graph,
    source_id: str,
) -> Tuple[Dict[str, object], ...]:

    src = _safe_str(source_id)

    return tuple(
        dict(e)
        for e in _safe_edges(None)
        if _safe_str(e.get("from")) == src
    )


def x_outgoing_edges__mutmut_6(
    graph: Graph,
    source_id: str,
) -> Tuple[Dict[str, object], ...]:

    src = _safe_str(source_id)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(None) == src
    )


def x_outgoing_edges__mutmut_7(
    graph: Graph,
    source_id: str,
) -> Tuple[Dict[str, object], ...]:

    src = _safe_str(source_id)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get(None)) == src
    )


def x_outgoing_edges__mutmut_8(
    graph: Graph,
    source_id: str,
) -> Tuple[Dict[str, object], ...]:

    src = _safe_str(source_id)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("XXfromXX")) == src
    )


def x_outgoing_edges__mutmut_9(
    graph: Graph,
    source_id: str,
) -> Tuple[Dict[str, object], ...]:

    src = _safe_str(source_id)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("FROM")) == src
    )


def x_outgoing_edges__mutmut_10(
    graph: Graph,
    source_id: str,
) -> Tuple[Dict[str, object], ...]:

    src = _safe_str(source_id)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("from")) != src
    )

x_outgoing_edges__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_outgoing_edges__mutmut_1': x_outgoing_edges__mutmut_1, 
    'x_outgoing_edges__mutmut_2': x_outgoing_edges__mutmut_2, 
    'x_outgoing_edges__mutmut_3': x_outgoing_edges__mutmut_3, 
    'x_outgoing_edges__mutmut_4': x_outgoing_edges__mutmut_4, 
    'x_outgoing_edges__mutmut_5': x_outgoing_edges__mutmut_5, 
    'x_outgoing_edges__mutmut_6': x_outgoing_edges__mutmut_6, 
    'x_outgoing_edges__mutmut_7': x_outgoing_edges__mutmut_7, 
    'x_outgoing_edges__mutmut_8': x_outgoing_edges__mutmut_8, 
    'x_outgoing_edges__mutmut_9': x_outgoing_edges__mutmut_9, 
    'x_outgoing_edges__mutmut_10': x_outgoing_edges__mutmut_10
}
x_outgoing_edges__mutmut_orig.__name__ = 'x_outgoing_edges'


def incoming_edges(
    graph: Graph,
    target_id: str,
) -> Tuple[Dict[str, object], ...]:
    args = [graph, target_id]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_incoming_edges__mutmut_orig, x_incoming_edges__mutmut_mutants, args, kwargs, None)


def x_incoming_edges__mutmut_orig(
    graph: Graph,
    target_id: str,
) -> Tuple[Dict[str, object], ...]:

    tgt = _safe_str(target_id)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("to")) == tgt
    )


def x_incoming_edges__mutmut_1(
    graph: Graph,
    target_id: str,
) -> Tuple[Dict[str, object], ...]:

    tgt = None

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("to")) == tgt
    )


def x_incoming_edges__mutmut_2(
    graph: Graph,
    target_id: str,
) -> Tuple[Dict[str, object], ...]:

    tgt = _safe_str(None)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("to")) == tgt
    )


def x_incoming_edges__mutmut_3(
    graph: Graph,
    target_id: str,
) -> Tuple[Dict[str, object], ...]:

    tgt = _safe_str(target_id)

    return tuple(
        None
    )


def x_incoming_edges__mutmut_4(
    graph: Graph,
    target_id: str,
) -> Tuple[Dict[str, object], ...]:

    tgt = _safe_str(target_id)

    return tuple(
        dict(None)
        for e in _safe_edges(graph)
        if _safe_str(e.get("to")) == tgt
    )


def x_incoming_edges__mutmut_5(
    graph: Graph,
    target_id: str,
) -> Tuple[Dict[str, object], ...]:

    tgt = _safe_str(target_id)

    return tuple(
        dict(e)
        for e in _safe_edges(None)
        if _safe_str(e.get("to")) == tgt
    )


def x_incoming_edges__mutmut_6(
    graph: Graph,
    target_id: str,
) -> Tuple[Dict[str, object], ...]:

    tgt = _safe_str(target_id)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(None) == tgt
    )


def x_incoming_edges__mutmut_7(
    graph: Graph,
    target_id: str,
) -> Tuple[Dict[str, object], ...]:

    tgt = _safe_str(target_id)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get(None)) == tgt
    )


def x_incoming_edges__mutmut_8(
    graph: Graph,
    target_id: str,
) -> Tuple[Dict[str, object], ...]:

    tgt = _safe_str(target_id)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("XXtoXX")) == tgt
    )


def x_incoming_edges__mutmut_9(
    graph: Graph,
    target_id: str,
) -> Tuple[Dict[str, object], ...]:

    tgt = _safe_str(target_id)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("TO")) == tgt
    )


def x_incoming_edges__mutmut_10(
    graph: Graph,
    target_id: str,
) -> Tuple[Dict[str, object], ...]:

    tgt = _safe_str(target_id)

    return tuple(
        dict(e)
        for e in _safe_edges(graph)
        if _safe_str(e.get("to")) != tgt
    )

x_incoming_edges__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_incoming_edges__mutmut_1': x_incoming_edges__mutmut_1, 
    'x_incoming_edges__mutmut_2': x_incoming_edges__mutmut_2, 
    'x_incoming_edges__mutmut_3': x_incoming_edges__mutmut_3, 
    'x_incoming_edges__mutmut_4': x_incoming_edges__mutmut_4, 
    'x_incoming_edges__mutmut_5': x_incoming_edges__mutmut_5, 
    'x_incoming_edges__mutmut_6': x_incoming_edges__mutmut_6, 
    'x_incoming_edges__mutmut_7': x_incoming_edges__mutmut_7, 
    'x_incoming_edges__mutmut_8': x_incoming_edges__mutmut_8, 
    'x_incoming_edges__mutmut_9': x_incoming_edges__mutmut_9, 
    'x_incoming_edges__mutmut_10': x_incoming_edges__mutmut_10
}
x_incoming_edges__mutmut_orig.__name__ = 'x_incoming_edges'


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def node_in_degree(graph: Graph) -> Dict[str, int]:
    args = [graph]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_node_in_degree__mutmut_orig, x_node_in_degree__mutmut_mutants, args, kwargs, None)


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_orig(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = _safe_str(e.get("to"))
        if target:
            counter[target] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_1(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = None

    for e in _safe_edges(graph):
        target = _safe_str(e.get("to"))
        if target:
            counter[target] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_2(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(None):
        target = _safe_str(e.get("to"))
        if target:
            counter[target] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_3(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = None
        if target:
            counter[target] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_4(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = _safe_str(None)
        if target:
            counter[target] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_5(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = _safe_str(e.get(None))
        if target:
            counter[target] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_6(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = _safe_str(e.get("XXtoXX"))
        if target:
            counter[target] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_7(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = _safe_str(e.get("TO"))
        if target:
            counter[target] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_8(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = _safe_str(e.get("to"))
        if target:
            counter[target] = 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_9(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = _safe_str(e.get("to"))
        if target:
            counter[target] -= 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_10(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = _safe_str(e.get("to"))
        if target:
            counter[target] += 2

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_11(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = _safe_str(e.get("to"))
        if target:
            counter[target] += 1

    return dict(None)


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_12(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = _safe_str(e.get("to"))
        if target:
            counter[target] += 1

    return dict(sorted(None, key=lambda i: (-i[1], i[0])))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_13(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = _safe_str(e.get("to"))
        if target:
            counter[target] += 1

    return dict(sorted(counter.items(), key=None))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_14(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = _safe_str(e.get("to"))
        if target:
            counter[target] += 1

    return dict(sorted(key=lambda i: (-i[1], i[0])))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_15(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = _safe_str(e.get("to"))
        if target:
            counter[target] += 1

    return dict(sorted(counter.items(), ))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_16(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = _safe_str(e.get("to"))
        if target:
            counter[target] += 1

    return dict(sorted(counter.items(), key=lambda i: None))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_17(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = _safe_str(e.get("to"))
        if target:
            counter[target] += 1

    return dict(sorted(counter.items(), key=lambda i: (+i[1], i[0])))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_18(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = _safe_str(e.get("to"))
        if target:
            counter[target] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[2], i[0])))


# =============================================================================
# DEGREE / CENTRALITY HELPERS
# =============================================================================

def x_node_in_degree__mutmut_19(graph: Graph) -> Dict[str, int]:
    """
    Compute in-degree (incoming edges) per node.

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        target = _safe_str(e.get("to"))
        if target:
            counter[target] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[1])))

x_node_in_degree__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_node_in_degree__mutmut_1': x_node_in_degree__mutmut_1, 
    'x_node_in_degree__mutmut_2': x_node_in_degree__mutmut_2, 
    'x_node_in_degree__mutmut_3': x_node_in_degree__mutmut_3, 
    'x_node_in_degree__mutmut_4': x_node_in_degree__mutmut_4, 
    'x_node_in_degree__mutmut_5': x_node_in_degree__mutmut_5, 
    'x_node_in_degree__mutmut_6': x_node_in_degree__mutmut_6, 
    'x_node_in_degree__mutmut_7': x_node_in_degree__mutmut_7, 
    'x_node_in_degree__mutmut_8': x_node_in_degree__mutmut_8, 
    'x_node_in_degree__mutmut_9': x_node_in_degree__mutmut_9, 
    'x_node_in_degree__mutmut_10': x_node_in_degree__mutmut_10, 
    'x_node_in_degree__mutmut_11': x_node_in_degree__mutmut_11, 
    'x_node_in_degree__mutmut_12': x_node_in_degree__mutmut_12, 
    'x_node_in_degree__mutmut_13': x_node_in_degree__mutmut_13, 
    'x_node_in_degree__mutmut_14': x_node_in_degree__mutmut_14, 
    'x_node_in_degree__mutmut_15': x_node_in_degree__mutmut_15, 
    'x_node_in_degree__mutmut_16': x_node_in_degree__mutmut_16, 
    'x_node_in_degree__mutmut_17': x_node_in_degree__mutmut_17, 
    'x_node_in_degree__mutmut_18': x_node_in_degree__mutmut_18, 
    'x_node_in_degree__mutmut_19': x_node_in_degree__mutmut_19
}
x_node_in_degree__mutmut_orig.__name__ = 'x_node_in_degree'


def node_out_degree(graph: Graph) -> Dict[str, int]:
    args = [graph]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_node_out_degree__mutmut_orig, x_node_out_degree__mutmut_mutants, args, kwargs, None)


def x_node_out_degree__mutmut_orig(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = _safe_str(e.get("from"))
        if source:
            counter[source] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


def x_node_out_degree__mutmut_1(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = None

    for e in _safe_edges(graph):
        source = _safe_str(e.get("from"))
        if source:
            counter[source] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


def x_node_out_degree__mutmut_2(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(None):
        source = _safe_str(e.get("from"))
        if source:
            counter[source] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


def x_node_out_degree__mutmut_3(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = None
        if source:
            counter[source] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


def x_node_out_degree__mutmut_4(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = _safe_str(None)
        if source:
            counter[source] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


def x_node_out_degree__mutmut_5(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = _safe_str(e.get(None))
        if source:
            counter[source] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


def x_node_out_degree__mutmut_6(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = _safe_str(e.get("XXfromXX"))
        if source:
            counter[source] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


def x_node_out_degree__mutmut_7(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = _safe_str(e.get("FROM"))
        if source:
            counter[source] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


def x_node_out_degree__mutmut_8(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = _safe_str(e.get("from"))
        if source:
            counter[source] = 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


def x_node_out_degree__mutmut_9(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = _safe_str(e.get("from"))
        if source:
            counter[source] -= 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


def x_node_out_degree__mutmut_10(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = _safe_str(e.get("from"))
        if source:
            counter[source] += 2

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[0])))


def x_node_out_degree__mutmut_11(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = _safe_str(e.get("from"))
        if source:
            counter[source] += 1

    return dict(None)


def x_node_out_degree__mutmut_12(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = _safe_str(e.get("from"))
        if source:
            counter[source] += 1

    return dict(sorted(None, key=lambda i: (-i[1], i[0])))


def x_node_out_degree__mutmut_13(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = _safe_str(e.get("from"))
        if source:
            counter[source] += 1

    return dict(sorted(counter.items(), key=None))


def x_node_out_degree__mutmut_14(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = _safe_str(e.get("from"))
        if source:
            counter[source] += 1

    return dict(sorted(key=lambda i: (-i[1], i[0])))


def x_node_out_degree__mutmut_15(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = _safe_str(e.get("from"))
        if source:
            counter[source] += 1

    return dict(sorted(counter.items(), ))


def x_node_out_degree__mutmut_16(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = _safe_str(e.get("from"))
        if source:
            counter[source] += 1

    return dict(sorted(counter.items(), key=lambda i: None))


def x_node_out_degree__mutmut_17(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = _safe_str(e.get("from"))
        if source:
            counter[source] += 1

    return dict(sorted(counter.items(), key=lambda i: (+i[1], i[0])))


def x_node_out_degree__mutmut_18(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = _safe_str(e.get("from"))
        if source:
            counter[source] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[2], i[0])))


def x_node_out_degree__mutmut_19(graph: Graph) -> Dict[str, int]:
    """
    Compute out-degree (outgoing edges) per node.
    """

    counter: Counter[str] = Counter()

    for e in _safe_edges(graph):
        source = _safe_str(e.get("from"))
        if source:
            counter[source] += 1

    return dict(sorted(counter.items(), key=lambda i: (-i[1], i[1])))

x_node_out_degree__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_node_out_degree__mutmut_1': x_node_out_degree__mutmut_1, 
    'x_node_out_degree__mutmut_2': x_node_out_degree__mutmut_2, 
    'x_node_out_degree__mutmut_3': x_node_out_degree__mutmut_3, 
    'x_node_out_degree__mutmut_4': x_node_out_degree__mutmut_4, 
    'x_node_out_degree__mutmut_5': x_node_out_degree__mutmut_5, 
    'x_node_out_degree__mutmut_6': x_node_out_degree__mutmut_6, 
    'x_node_out_degree__mutmut_7': x_node_out_degree__mutmut_7, 
    'x_node_out_degree__mutmut_8': x_node_out_degree__mutmut_8, 
    'x_node_out_degree__mutmut_9': x_node_out_degree__mutmut_9, 
    'x_node_out_degree__mutmut_10': x_node_out_degree__mutmut_10, 
    'x_node_out_degree__mutmut_11': x_node_out_degree__mutmut_11, 
    'x_node_out_degree__mutmut_12': x_node_out_degree__mutmut_12, 
    'x_node_out_degree__mutmut_13': x_node_out_degree__mutmut_13, 
    'x_node_out_degree__mutmut_14': x_node_out_degree__mutmut_14, 
    'x_node_out_degree__mutmut_15': x_node_out_degree__mutmut_15, 
    'x_node_out_degree__mutmut_16': x_node_out_degree__mutmut_16, 
    'x_node_out_degree__mutmut_17': x_node_out_degree__mutmut_17, 
    'x_node_out_degree__mutmut_18': x_node_out_degree__mutmut_18, 
    'x_node_out_degree__mutmut_19': x_node_out_degree__mutmut_19
}
x_node_out_degree__mutmut_orig.__name__ = 'x_node_out_degree'


# =============================================================================
# REFERENCE ANALYSIS
# =============================================================================

def reference_counts(graph: Graph) -> Dict[str, int]:
    args = [graph]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_reference_counts__mutmut_orig, x_reference_counts__mutmut_mutants, args, kwargs, None)


# =============================================================================
# REFERENCE ANALYSIS
# =============================================================================

def x_reference_counts__mutmut_orig(graph: Graph) -> Dict[str, int]:
    """
    Count references by target node.

    ✅ Deterministic
    """
    return node_in_degree(graph)


# =============================================================================
# REFERENCE ANALYSIS
# =============================================================================

def x_reference_counts__mutmut_1(graph: Graph) -> Dict[str, int]:
    """
    Count references by target node.

    ✅ Deterministic
    """
    return node_in_degree(None)

x_reference_counts__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_reference_counts__mutmut_1': x_reference_counts__mutmut_1
}
x_reference_counts__mutmut_orig.__name__ = 'x_reference_counts'


def top_referenced_nodes(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    args = [graph, limit]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_top_referenced_nodes__mutmut_orig, x_top_referenced_nodes__mutmut_mutants, args, kwargs, None)


def x_top_referenced_nodes__mutmut_orig(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_1(
    graph: Graph,
    limit: int = 11,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_2(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = None

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_3(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(None)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_4(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = None

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_5(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(None)[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_6(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(None, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_7(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, None)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_8(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_9(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, )]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_10(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 1)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_11(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        None
    )


def x_top_referenced_nodes__mutmut_12(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "XXidXX": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_13(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "ID": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_14(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "XXreference_countXX": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_15(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "REFERENCE_COUNT": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_16(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "XXgraph_statusXX": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_17(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "GRAPH_STATUS": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_18(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "XXgraph_classificationXX": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_19(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "GRAPH_CLASSIFICATION": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_20(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "XXread_onlyXX": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_21(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "READ_ONLY": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_22(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "XXdisplay_onlyXX": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_23(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "DISPLAY_ONLY": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_24(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "XXobservational_onlyXX": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_25(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "OBSERVATIONAL_ONLY": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_26(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "XXrepresentation_onlyXX": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_27(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "REPRESENTATION_ONLY": REPRESENTATION_ONLY,

            "authoritative": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_28(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "XXauthoritativeXX": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_29(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "AUTHORITATIVE": False,
        }
        for node_id, count in ranked
    )


def x_top_referenced_nodes__mutmut_30(
    graph: Graph,
    limit: int = 10,
) -> Tuple[Dict[str, object], ...]:
    """
    Rank most referenced nodes.

    ✅ Observational ranking
    ✅ Not authority
    """

    counts = reference_counts(graph)

    ranked = list(counts.items())[: max(limit, 0)]

    return tuple(
        {
            "id": node_id,
            "reference_count": count,

            # metadata
            "graph_status": GRAPH_STATUS,
            "graph_classification": GRAPH_CLASSIFICATION,

            # flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "representation_only": REPRESENTATION_ONLY,

            "authoritative": True,
        }
        for node_id, count in ranked
    )

x_top_referenced_nodes__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_top_referenced_nodes__mutmut_1': x_top_referenced_nodes__mutmut_1, 
    'x_top_referenced_nodes__mutmut_2': x_top_referenced_nodes__mutmut_2, 
    'x_top_referenced_nodes__mutmut_3': x_top_referenced_nodes__mutmut_3, 
    'x_top_referenced_nodes__mutmut_4': x_top_referenced_nodes__mutmut_4, 
    'x_top_referenced_nodes__mutmut_5': x_top_referenced_nodes__mutmut_5, 
    'x_top_referenced_nodes__mutmut_6': x_top_referenced_nodes__mutmut_6, 
    'x_top_referenced_nodes__mutmut_7': x_top_referenced_nodes__mutmut_7, 
    'x_top_referenced_nodes__mutmut_8': x_top_referenced_nodes__mutmut_8, 
    'x_top_referenced_nodes__mutmut_9': x_top_referenced_nodes__mutmut_9, 
    'x_top_referenced_nodes__mutmut_10': x_top_referenced_nodes__mutmut_10, 
    'x_top_referenced_nodes__mutmut_11': x_top_referenced_nodes__mutmut_11, 
    'x_top_referenced_nodes__mutmut_12': x_top_referenced_nodes__mutmut_12, 
    'x_top_referenced_nodes__mutmut_13': x_top_referenced_nodes__mutmut_13, 
    'x_top_referenced_nodes__mutmut_14': x_top_referenced_nodes__mutmut_14, 
    'x_top_referenced_nodes__mutmut_15': x_top_referenced_nodes__mutmut_15, 
    'x_top_referenced_nodes__mutmut_16': x_top_referenced_nodes__mutmut_16, 
    'x_top_referenced_nodes__mutmut_17': x_top_referenced_nodes__mutmut_17, 
    'x_top_referenced_nodes__mutmut_18': x_top_referenced_nodes__mutmut_18, 
    'x_top_referenced_nodes__mutmut_19': x_top_referenced_nodes__mutmut_19, 
    'x_top_referenced_nodes__mutmut_20': x_top_referenced_nodes__mutmut_20, 
    'x_top_referenced_nodes__mutmut_21': x_top_referenced_nodes__mutmut_21, 
    'x_top_referenced_nodes__mutmut_22': x_top_referenced_nodes__mutmut_22, 
    'x_top_referenced_nodes__mutmut_23': x_top_referenced_nodes__mutmut_23, 
    'x_top_referenced_nodes__mutmut_24': x_top_referenced_nodes__mutmut_24, 
    'x_top_referenced_nodes__mutmut_25': x_top_referenced_nodes__mutmut_25, 
    'x_top_referenced_nodes__mutmut_26': x_top_referenced_nodes__mutmut_26, 
    'x_top_referenced_nodes__mutmut_27': x_top_referenced_nodes__mutmut_27, 
    'x_top_referenced_nodes__mutmut_28': x_top_referenced_nodes__mutmut_28, 
    'x_top_referenced_nodes__mutmut_29': x_top_referenced_nodes__mutmut_29, 
    'x_top_referenced_nodes__mutmut_30': x_top_referenced_nodes__mutmut_30
}
x_top_referenced_nodes__mutmut_orig.__name__ = 'x_top_referenced_nodes'


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def connected_nodes(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    args = [graph, node_id]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_connected_nodes__mutmut_orig, x_connected_nodes__mutmut_mutants, args, kwargs, None)


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_orig(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(e.get("to"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_1(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = None
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(e.get("to"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_2(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(None)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(e.get("to"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_3(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = None

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(e.get("to"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_4(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(None):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(e.get("to"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_5(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = None
        tgt = _safe_str(e.get("to"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_6(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(None)
        tgt = _safe_str(e.get("to"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_7(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get(None))
        tgt = _safe_str(e.get("to"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_8(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("XXfromXX"))
        tgt = _safe_str(e.get("to"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_9(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("FROM"))
        tgt = _safe_str(e.get("to"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_10(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = None

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_11(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(None)

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_12(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(e.get(None))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_13(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(e.get("XXtoXX"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_14(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(e.get("TO"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_15(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(e.get("to"))

        if src == nid or tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_16(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(e.get("to"))

        if src != nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_17(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(e.get("to"))

        if src == nid and tgt:
            result.append(None)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_18(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(e.get("to"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid or src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_19(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(e.get("to"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt != nid and src:
            result.append(src)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_20(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(e.get("to"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(None)

    return tuple(sorted(set(result)))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_21(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(e.get("to"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(None)


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_22(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(e.get("to"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(None))


# =============================================================================
# CONNECTIVITY HELPERS
# =============================================================================

def x_connected_nodes__mutmut_23(
    graph: Graph,
    node_id: str,
) -> Tuple[str, ...]:
    """
    Return all nodes connected to a given node.

    ✅ Observational traversal
    """

    nid = _safe_str(node_id)
    result: List[str] = []

    for e in _safe_edges(graph):
        src = _safe_str(e.get("from"))
        tgt = _safe_str(e.get("to"))

        if src == nid and tgt:
            result.append(tgt)
        elif tgt == nid and src:
            result.append(src)

    return tuple(sorted(set(None)))

x_connected_nodes__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_connected_nodes__mutmut_1': x_connected_nodes__mutmut_1, 
    'x_connected_nodes__mutmut_2': x_connected_nodes__mutmut_2, 
    'x_connected_nodes__mutmut_3': x_connected_nodes__mutmut_3, 
    'x_connected_nodes__mutmut_4': x_connected_nodes__mutmut_4, 
    'x_connected_nodes__mutmut_5': x_connected_nodes__mutmut_5, 
    'x_connected_nodes__mutmut_6': x_connected_nodes__mutmut_6, 
    'x_connected_nodes__mutmut_7': x_connected_nodes__mutmut_7, 
    'x_connected_nodes__mutmut_8': x_connected_nodes__mutmut_8, 
    'x_connected_nodes__mutmut_9': x_connected_nodes__mutmut_9, 
    'x_connected_nodes__mutmut_10': x_connected_nodes__mutmut_10, 
    'x_connected_nodes__mutmut_11': x_connected_nodes__mutmut_11, 
    'x_connected_nodes__mutmut_12': x_connected_nodes__mutmut_12, 
    'x_connected_nodes__mutmut_13': x_connected_nodes__mutmut_13, 
    'x_connected_nodes__mutmut_14': x_connected_nodes__mutmut_14, 
    'x_connected_nodes__mutmut_15': x_connected_nodes__mutmut_15, 
    'x_connected_nodes__mutmut_16': x_connected_nodes__mutmut_16, 
    'x_connected_nodes__mutmut_17': x_connected_nodes__mutmut_17, 
    'x_connected_nodes__mutmut_18': x_connected_nodes__mutmut_18, 
    'x_connected_nodes__mutmut_19': x_connected_nodes__mutmut_19, 
    'x_connected_nodes__mutmut_20': x_connected_nodes__mutmut_20, 
    'x_connected_nodes__mutmut_21': x_connected_nodes__mutmut_21, 
    'x_connected_nodes__mutmut_22': x_connected_nodes__mutmut_22, 
    'x_connected_nodes__mutmut_23': x_connected_nodes__mutmut_23
}
x_connected_nodes__mutmut_orig.__name__ = 'x_connected_nodes'


# =============================================================================
# SUMMARY
# =============================================================================

def build_graph_query_summary(graph: Graph) -> Dict[str, object]:
    args = [graph]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_graph_query_summary__mutmut_orig, x_build_graph_query_summary__mutmut_mutants, args, kwargs, None)


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_orig(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_1(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = None
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_2(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(None)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_3(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = None

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_4(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(None)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_5(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = None
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_6(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(None)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_7(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = None

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_8(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(None)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_9(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "XXstatusXX": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_10(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "STATUS": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_11(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "XXgraph_statusXX": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_12(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "GRAPH_STATUS": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_13(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "XXgraph_classificationXX": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_14(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "GRAPH_CLASSIFICATION": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_15(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "XXread_onlyXX": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_16(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "READ_ONLY": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_17(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "XXdisplay_onlyXX": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_18(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "DISPLAY_ONLY": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_19(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "XXobservational_onlyXX": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_20(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "OBSERVATIONAL_ONLY": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_21(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "XXrepresentation_onlyXX": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_22(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "REPRESENTATION_ONLY": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_23(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "XXauthoritativeXX": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_24(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "AUTHORITATIVE": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_25(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": True,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_26(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "XXnode_countXX": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_27(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "NODE_COUNT": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_28(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "XXedge_countXX": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_29(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "EDGE_COUNT": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_30(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "XXexecution_node_countXX": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_31(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "EXECUTION_NODE_COUNT": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_32(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "XXgovernance_node_countXX": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_33(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "GOVERNANCE_NODE_COUNT": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_34(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "XXreference_countsXX": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_35(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "REFERENCE_COUNTS": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_36(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(None),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_37(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "XXtop_referenced_nodesXX": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_38(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "TOP_REFERENCED_NODES": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_39(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(None),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_40(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "XXin_degreeXX": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_41(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "IN_DEGREE": node_in_degree(graph),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_42(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(None),
        "out_degree": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_43(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "XXout_degreeXX": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_44(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "OUT_DEGREE": node_out_degree(graph),
    }


# =============================================================================
# SUMMARY
# =============================================================================

def x_build_graph_query_summary__mutmut_45(graph: Graph) -> Dict[str, object]:
    """
    Build canonical graph summary.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    nodes = _safe_nodes(graph)
    edges = _safe_edges(graph)

    exec_nodes = execution_nodes(graph)
    gov_nodes = governance_nodes(graph)

    return {
        "status": GRAPH_STATUS,
        "graph_status": GRAPH_STATUS,
        "graph_classification": GRAPH_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "authoritative": False,

        # counts
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_node_count": len(exec_nodes),
        "governance_node_count": len(gov_nodes),

        # analysis
        "reference_counts": reference_counts(graph),
        "top_referenced_nodes": top_referenced_nodes(graph),

        # graph structure
        "in_degree": node_in_degree(graph),
        "out_degree": node_out_degree(None),
    }

x_build_graph_query_summary__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_graph_query_summary__mutmut_1': x_build_graph_query_summary__mutmut_1, 
    'x_build_graph_query_summary__mutmut_2': x_build_graph_query_summary__mutmut_2, 
    'x_build_graph_query_summary__mutmut_3': x_build_graph_query_summary__mutmut_3, 
    'x_build_graph_query_summary__mutmut_4': x_build_graph_query_summary__mutmut_4, 
    'x_build_graph_query_summary__mutmut_5': x_build_graph_query_summary__mutmut_5, 
    'x_build_graph_query_summary__mutmut_6': x_build_graph_query_summary__mutmut_6, 
    'x_build_graph_query_summary__mutmut_7': x_build_graph_query_summary__mutmut_7, 
    'x_build_graph_query_summary__mutmut_8': x_build_graph_query_summary__mutmut_8, 
    'x_build_graph_query_summary__mutmut_9': x_build_graph_query_summary__mutmut_9, 
    'x_build_graph_query_summary__mutmut_10': x_build_graph_query_summary__mutmut_10, 
    'x_build_graph_query_summary__mutmut_11': x_build_graph_query_summary__mutmut_11, 
    'x_build_graph_query_summary__mutmut_12': x_build_graph_query_summary__mutmut_12, 
    'x_build_graph_query_summary__mutmut_13': x_build_graph_query_summary__mutmut_13, 
    'x_build_graph_query_summary__mutmut_14': x_build_graph_query_summary__mutmut_14, 
    'x_build_graph_query_summary__mutmut_15': x_build_graph_query_summary__mutmut_15, 
    'x_build_graph_query_summary__mutmut_16': x_build_graph_query_summary__mutmut_16, 
    'x_build_graph_query_summary__mutmut_17': x_build_graph_query_summary__mutmut_17, 
    'x_build_graph_query_summary__mutmut_18': x_build_graph_query_summary__mutmut_18, 
    'x_build_graph_query_summary__mutmut_19': x_build_graph_query_summary__mutmut_19, 
    'x_build_graph_query_summary__mutmut_20': x_build_graph_query_summary__mutmut_20, 
    'x_build_graph_query_summary__mutmut_21': x_build_graph_query_summary__mutmut_21, 
    'x_build_graph_query_summary__mutmut_22': x_build_graph_query_summary__mutmut_22, 
    'x_build_graph_query_summary__mutmut_23': x_build_graph_query_summary__mutmut_23, 
    'x_build_graph_query_summary__mutmut_24': x_build_graph_query_summary__mutmut_24, 
    'x_build_graph_query_summary__mutmut_25': x_build_graph_query_summary__mutmut_25, 
    'x_build_graph_query_summary__mutmut_26': x_build_graph_query_summary__mutmut_26, 
    'x_build_graph_query_summary__mutmut_27': x_build_graph_query_summary__mutmut_27, 
    'x_build_graph_query_summary__mutmut_28': x_build_graph_query_summary__mutmut_28, 
    'x_build_graph_query_summary__mutmut_29': x_build_graph_query_summary__mutmut_29, 
    'x_build_graph_query_summary__mutmut_30': x_build_graph_query_summary__mutmut_30, 
    'x_build_graph_query_summary__mutmut_31': x_build_graph_query_summary__mutmut_31, 
    'x_build_graph_query_summary__mutmut_32': x_build_graph_query_summary__mutmut_32, 
    'x_build_graph_query_summary__mutmut_33': x_build_graph_query_summary__mutmut_33, 
    'x_build_graph_query_summary__mutmut_34': x_build_graph_query_summary__mutmut_34, 
    'x_build_graph_query_summary__mutmut_35': x_build_graph_query_summary__mutmut_35, 
    'x_build_graph_query_summary__mutmut_36': x_build_graph_query_summary__mutmut_36, 
    'x_build_graph_query_summary__mutmut_37': x_build_graph_query_summary__mutmut_37, 
    'x_build_graph_query_summary__mutmut_38': x_build_graph_query_summary__mutmut_38, 
    'x_build_graph_query_summary__mutmut_39': x_build_graph_query_summary__mutmut_39, 
    'x_build_graph_query_summary__mutmut_40': x_build_graph_query_summary__mutmut_40, 
    'x_build_graph_query_summary__mutmut_41': x_build_graph_query_summary__mutmut_41, 
    'x_build_graph_query_summary__mutmut_42': x_build_graph_query_summary__mutmut_42, 
    'x_build_graph_query_summary__mutmut_43': x_build_graph_query_summary__mutmut_43, 
    'x_build_graph_query_summary__mutmut_44': x_build_graph_query_summary__mutmut_44, 
    'x_build_graph_query_summary__mutmut_45': x_build_graph_query_summary__mutmut_45
}
x_build_graph_query_summary__mutmut_orig.__name__ = 'x_build_graph_query_summary'


# =============================================================================
# INTEGRITY
# =============================================================================

def assert_graph_query_integrity(graph: Graph) -> None:
    args = [graph]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_assert_graph_query_integrity__mutmut_orig, x_assert_graph_query_integrity__mutmut_mutants, args, kwargs, None)


# =============================================================================
# INTEGRITY
# =============================================================================

def x_assert_graph_query_integrity__mutmut_orig(graph: Graph) -> None:
    """
    Ensure query never produces authority.

    Raises:
        RuntimeError if violation detected
    """

    if graph.get("authoritative") is True:
        raise RuntimeError("Graph query must not operate on authoritative graph")


# =============================================================================
# INTEGRITY
# =============================================================================

def x_assert_graph_query_integrity__mutmut_1(graph: Graph) -> None:
    """
    Ensure query never produces authority.

    Raises:
        RuntimeError if violation detected
    """

    if graph.get(None) is True:
        raise RuntimeError("Graph query must not operate on authoritative graph")


# =============================================================================
# INTEGRITY
# =============================================================================

def x_assert_graph_query_integrity__mutmut_2(graph: Graph) -> None:
    """
    Ensure query never produces authority.

    Raises:
        RuntimeError if violation detected
    """

    if graph.get("XXauthoritativeXX") is True:
        raise RuntimeError("Graph query must not operate on authoritative graph")


# =============================================================================
# INTEGRITY
# =============================================================================

def x_assert_graph_query_integrity__mutmut_3(graph: Graph) -> None:
    """
    Ensure query never produces authority.

    Raises:
        RuntimeError if violation detected
    """

    if graph.get("AUTHORITATIVE") is True:
        raise RuntimeError("Graph query must not operate on authoritative graph")


# =============================================================================
# INTEGRITY
# =============================================================================

def x_assert_graph_query_integrity__mutmut_4(graph: Graph) -> None:
    """
    Ensure query never produces authority.

    Raises:
        RuntimeError if violation detected
    """

    if graph.get("authoritative") is not True:
        raise RuntimeError("Graph query must not operate on authoritative graph")


# =============================================================================
# INTEGRITY
# =============================================================================

def x_assert_graph_query_integrity__mutmut_5(graph: Graph) -> None:
    """
    Ensure query never produces authority.

    Raises:
        RuntimeError if violation detected
    """

    if graph.get("authoritative") is False:
        raise RuntimeError("Graph query must not operate on authoritative graph")


# =============================================================================
# INTEGRITY
# =============================================================================

def x_assert_graph_query_integrity__mutmut_6(graph: Graph) -> None:
    """
    Ensure query never produces authority.

    Raises:
        RuntimeError if violation detected
    """

    if graph.get("authoritative") is True:
        raise RuntimeError(None)


# =============================================================================
# INTEGRITY
# =============================================================================

def x_assert_graph_query_integrity__mutmut_7(graph: Graph) -> None:
    """
    Ensure query never produces authority.

    Raises:
        RuntimeError if violation detected
    """

    if graph.get("authoritative") is True:
        raise RuntimeError("XXGraph query must not operate on authoritative graphXX")


# =============================================================================
# INTEGRITY
# =============================================================================

def x_assert_graph_query_integrity__mutmut_8(graph: Graph) -> None:
    """
    Ensure query never produces authority.

    Raises:
        RuntimeError if violation detected
    """

    if graph.get("authoritative") is True:
        raise RuntimeError("graph query must not operate on authoritative graph")


# =============================================================================
# INTEGRITY
# =============================================================================

def x_assert_graph_query_integrity__mutmut_9(graph: Graph) -> None:
    """
    Ensure query never produces authority.

    Raises:
        RuntimeError if violation detected
    """

    if graph.get("authoritative") is True:
        raise RuntimeError("GRAPH QUERY MUST NOT OPERATE ON AUTHORITATIVE GRAPH")

x_assert_graph_query_integrity__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_assert_graph_query_integrity__mutmut_1': x_assert_graph_query_integrity__mutmut_1, 
    'x_assert_graph_query_integrity__mutmut_2': x_assert_graph_query_integrity__mutmut_2, 
    'x_assert_graph_query_integrity__mutmut_3': x_assert_graph_query_integrity__mutmut_3, 
    'x_assert_graph_query_integrity__mutmut_4': x_assert_graph_query_integrity__mutmut_4, 
    'x_assert_graph_query_integrity__mutmut_5': x_assert_graph_query_integrity__mutmut_5, 
    'x_assert_graph_query_integrity__mutmut_6': x_assert_graph_query_integrity__mutmut_6, 
    'x_assert_graph_query_integrity__mutmut_7': x_assert_graph_query_integrity__mutmut_7, 
    'x_assert_graph_query_integrity__mutmut_8': x_assert_graph_query_integrity__mutmut_8, 
    'x_assert_graph_query_integrity__mutmut_9': x_assert_graph_query_integrity__mutmut_9
}
x_assert_graph_query_integrity__mutmut_orig.__name__ = 'x_assert_graph_query_integrity'


# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    "count_nodes",
    "count_edges",
    "nodes_by_type",
    "execution_nodes",
    "governance_nodes",
    "edges_by_relation",
    "outgoing_edges",
    "incoming_edges",
    "node_in_degree",
    "node_out_degree",
    "reference_counts",
    "top_referenced_nodes",
    "connected_nodes",
    "build_graph_query_summary",
    "assert_graph_query_integrity",
]