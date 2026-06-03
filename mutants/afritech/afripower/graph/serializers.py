"""
AFRIPower Graph Serializers

Read-only serializers for AFRIPower graph representations.

Graph serialization is strictly:
✅ display-only
✅ observational
✅ non-authoritative
"""

from __future__ import annotations
from typing import Any, Dict

# -----------------------------------------------------------------------------
# Optional DRF Import
# -----------------------------------------------------------------------------

try:
    from rest_framework import serializers
except Exception:  # pragma: no cover
    serializers = None  # type: ignore[assignment]
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
# FALLBACK SERIALIZATION (PURE PYTHON)
# =============================================================================

def serialize_graph_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    args = [payload]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_serialize_graph_payload__mutmut_orig, x_serialize_graph_payload__mutmut_mutants, args, kwargs, None)


# =============================================================================
# FALLBACK SERIALIZATION (PURE PYTHON)
# =============================================================================

def x_serialize_graph_payload__mutmut_orig(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pure serializer fallback.

    ✅ No validation
    ✅ No mutation
    ✅ Safe for non-DRF environments
    """

    if not isinstance(payload, dict):
        return {}

    return dict(payload)


# =============================================================================
# FALLBACK SERIALIZATION (PURE PYTHON)
# =============================================================================

def x_serialize_graph_payload__mutmut_1(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pure serializer fallback.

    ✅ No validation
    ✅ No mutation
    ✅ Safe for non-DRF environments
    """

    if isinstance(payload, dict):
        return {}

    return dict(payload)


# =============================================================================
# FALLBACK SERIALIZATION (PURE PYTHON)
# =============================================================================

def x_serialize_graph_payload__mutmut_2(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pure serializer fallback.

    ✅ No validation
    ✅ No mutation
    ✅ Safe for non-DRF environments
    """

    if not isinstance(payload, dict):
        return {}

    return dict(None)

x_serialize_graph_payload__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_serialize_graph_payload__mutmut_1': x_serialize_graph_payload__mutmut_1, 
    'x_serialize_graph_payload__mutmut_2': x_serialize_graph_payload__mutmut_2
}
x_serialize_graph_payload__mutmut_orig.__name__ = 'x_serialize_graph_payload'


# =============================================================================
# DRF SERIALIZERS (READ-ONLY ONLY)
# =============================================================================

if serializers is not None:

    # -------------------------------------------------------------------------
    # NODE
    # -------------------------------------------------------------------------

    class GraphNodeSerializer(serializers.Serializer):
        id = serializers.CharField(read_only=True)
        type = serializers.CharField(read_only=True)
        label = serializers.CharField(read_only=True, required=False)
        metadata = serializers.DictField(read_only=True, required=False)

        graph_status = serializers.CharField(read_only=True, required=False)
        graph_classification = serializers.CharField(read_only=True, required=False)

        read_only = serializers.BooleanField(read_only=True)
        display_only = serializers.BooleanField(read_only=True)
        observational_only = serializers.BooleanField(read_only=True)
        representation_only = serializers.BooleanField(read_only=True)
        authoritative = serializers.BooleanField(read_only=True)


    # -------------------------------------------------------------------------
    # EDGE
    # -------------------------------------------------------------------------

    class GraphEdgeSerializer(serializers.Serializer):
        """
        Handles BOTH:
        - projection format → "from","to"
        - model format → "source","target"
        """

        # unified normalized fields (always present in output)
        source = serializers.SerializerMethodField()
        target = serializers.SerializerMethodField()

        # raw compatibility fields
        from_node = serializers.CharField(source="from", read_only=True, required=False)
        to_node = serializers.CharField(source="to", read_only=True, required=False)

        relation = serializers.CharField(read_only=True)
        metadata = serializers.DictField(read_only=True, required=False)

        graph_status = serializers.CharField(read_only=True, required=False)
        graph_classification = serializers.CharField(read_only=True, required=False)

        read_only = serializers.BooleanField(read_only=True)
        display_only = serializers.BooleanField(read_only=True)
        observational_only = serializers.BooleanField(read_only=True)
        representation_only = serializers.BooleanField(read_only=True)
        authoritative = serializers.BooleanField(read_only=True)

        def get_source(self, obj):
            return (
                obj.get("source")
                or obj.get("from")
                or ""
            )

        def get_target(self, obj):
            return (
                obj.get("target")
                or obj.get("to")
                or ""
            )


    # -------------------------------------------------------------------------
    # METADATA
    # -------------------------------------------------------------------------

    class GraphMetadataSerializer(serializers.Serializer):
        execution_count = serializers.IntegerField(read_only=True, required=False)
        reference_count = serializers.IntegerField(read_only=True, required=False)
        node_count = serializers.IntegerField(read_only=True, required=False)
        edge_count = serializers.IntegerField(read_only=True, required=False)
        receipt_count_observed = serializers.IntegerField(read_only=True, required=False)

        representation_only = serializers.BooleanField(read_only=True)
        authoritative = serializers.BooleanField(read_only=True)


    # -------------------------------------------------------------------------
    # QUERY NODE
    # -------------------------------------------------------------------------

    class GraphQueryReferencedNodeSerializer(serializers.Serializer):
        id = serializers.CharField(read_only=True)
        reference_count = serializers.IntegerField(read_only=True)

        graph_status = serializers.CharField(read_only=True, required=False)
        graph_classification = serializers.CharField(read_only=True, required=False)

        read_only = serializers.BooleanField(read_only=True)
        display_only = serializers.BooleanField(read_only=True)
        observational_only = serializers.BooleanField(read_only=True)
        representation_only = serializers.BooleanField(read_only=True)
        authoritative = serializers.BooleanField(read_only=True)


    # -------------------------------------------------------------------------
    # PROJECTION
    # -------------------------------------------------------------------------

    class GraphProjectionSerializer(serializers.Serializer):
        status = serializers.CharField(read_only=True)
        graph_status = serializers.CharField(read_only=True)
        graph_classification = serializers.CharField(read_only=True)

        read_only = serializers.BooleanField(read_only=True)
        display_only = serializers.BooleanField(read_only=True)
        observational_only = serializers.BooleanField(read_only=True)
        representation_only = serializers.BooleanField(read_only=True)
        authoritative = serializers.BooleanField(read_only=True)

        nodes = GraphNodeSerializer(many=True, read_only=True)
        edges = GraphEdgeSerializer(many=True, read_only=True)
        metadata = GraphMetadataSerializer(read_only=True)


    # -------------------------------------------------------------------------
    # QUERY SUMMARY
    # -------------------------------------------------------------------------

    class GraphQuerySummarySerializer(serializers.Serializer):
        status = serializers.CharField(read_only=True)
        graph_status = serializers.CharField(read_only=True)
        graph_classification = serializers.CharField(read_only=True)

        read_only = serializers.BooleanField(read_only=True)
        display_only = serializers.BooleanField(read_only=True)
        observational_only = serializers.BooleanField(read_only=True)
        representation_only = serializers.BooleanField(read_only=True)
        authoritative = serializers.BooleanField(read_only=True)

        node_count = serializers.IntegerField(read_only=True)
        edge_count = serializers.IntegerField(read_only=True)
        execution_node_count = serializers.IntegerField(read_only=True)
        governance_node_count = serializers.IntegerField(read_only=True)

        reference_counts = serializers.DictField(
            child=serializers.IntegerField(),
            read_only=True,
        )

        top_referenced_nodes = GraphQueryReferencedNodeSerializer(
            many=True,
            read_only=True,
        )


    # -------------------------------------------------------------------------
    # SERIALIZATION ENTRY POINT
    # -------------------------------------------------------------------------

    def serialize_graph_with_drf(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize graph using DRF safely.

        ✅ No validation enforcement
        ✅ Read-only representation
        """

        if "nodes" in payload and "edges" in payload:
            serializer = GraphProjectionSerializer(payload)
        else:
            serializer = GraphQuerySummarySerializer(payload)

        return serializer.data

else:
    # -----------------------------------------------------------------------------
    # FALLBACK DEFINITIONS
    # -----------------------------------------------------------------------------

    GraphNodeSerializer = None  # type: ignore
    GraphEdgeSerializer = None  # type: ignore
    GraphProjectionSerializer = None  # type: ignore
    GraphQuerySummarySerializer = None  # type: ignore

    def serialize_graph_with_drf(payload: Dict[str, Any]) -> Dict[str, Any]:
        return serialize_graph_payload(payload)


# =============================================================================
# UNIFIED PUBLIC API
# =============================================================================

def serialize_graph(
    payload: Dict[str, Any],
    use_drf: bool = True,
) -> Dict[str, Any]:
    args = [payload, use_drf]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_serialize_graph__mutmut_orig, x_serialize_graph__mutmut_mutants, args, kwargs, None)


# =============================================================================
# UNIFIED PUBLIC API
# =============================================================================

def x_serialize_graph__mutmut_orig(
    payload: Dict[str, Any],
    use_drf: bool = True,
) -> Dict[str, Any]:
    """
    Unified graph serializer.

    ✅ Works with or without DRF
    ✅ No mutation
    ✅ No authority
    """

    if not isinstance(payload, dict):
        return {}

    if use_drf and serializers is not None:
        return serialize_graph_with_drf(payload)

    return serialize_graph_payload(payload)


# =============================================================================
# UNIFIED PUBLIC API
# =============================================================================

def x_serialize_graph__mutmut_1(
    payload: Dict[str, Any],
    use_drf: bool = False,
) -> Dict[str, Any]:
    """
    Unified graph serializer.

    ✅ Works with or without DRF
    ✅ No mutation
    ✅ No authority
    """

    if not isinstance(payload, dict):
        return {}

    if use_drf and serializers is not None:
        return serialize_graph_with_drf(payload)

    return serialize_graph_payload(payload)


# =============================================================================
# UNIFIED PUBLIC API
# =============================================================================

def x_serialize_graph__mutmut_2(
    payload: Dict[str, Any],
    use_drf: bool = True,
) -> Dict[str, Any]:
    """
    Unified graph serializer.

    ✅ Works with or without DRF
    ✅ No mutation
    ✅ No authority
    """

    if isinstance(payload, dict):
        return {}

    if use_drf and serializers is not None:
        return serialize_graph_with_drf(payload)

    return serialize_graph_payload(payload)


# =============================================================================
# UNIFIED PUBLIC API
# =============================================================================

def x_serialize_graph__mutmut_3(
    payload: Dict[str, Any],
    use_drf: bool = True,
) -> Dict[str, Any]:
    """
    Unified graph serializer.

    ✅ Works with or without DRF
    ✅ No mutation
    ✅ No authority
    """

    if not isinstance(payload, dict):
        return {}

    if use_drf or serializers is not None:
        return serialize_graph_with_drf(payload)

    return serialize_graph_payload(payload)


# =============================================================================
# UNIFIED PUBLIC API
# =============================================================================

def x_serialize_graph__mutmut_4(
    payload: Dict[str, Any],
    use_drf: bool = True,
) -> Dict[str, Any]:
    """
    Unified graph serializer.

    ✅ Works with or without DRF
    ✅ No mutation
    ✅ No authority
    """

    if not isinstance(payload, dict):
        return {}

    if use_drf and serializers is None:
        return serialize_graph_with_drf(payload)

    return serialize_graph_payload(payload)


# =============================================================================
# UNIFIED PUBLIC API
# =============================================================================

def x_serialize_graph__mutmut_5(
    payload: Dict[str, Any],
    use_drf: bool = True,
) -> Dict[str, Any]:
    """
    Unified graph serializer.

    ✅ Works with or without DRF
    ✅ No mutation
    ✅ No authority
    """

    if not isinstance(payload, dict):
        return {}

    if use_drf and serializers is not None:
        return serialize_graph_with_drf(None)

    return serialize_graph_payload(payload)


# =============================================================================
# UNIFIED PUBLIC API
# =============================================================================

def x_serialize_graph__mutmut_6(
    payload: Dict[str, Any],
    use_drf: bool = True,
) -> Dict[str, Any]:
    """
    Unified graph serializer.

    ✅ Works with or without DRF
    ✅ No mutation
    ✅ No authority
    """

    if not isinstance(payload, dict):
        return {}

    if use_drf and serializers is not None:
        return serialize_graph_with_drf(payload)

    return serialize_graph_payload(None)

x_serialize_graph__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_serialize_graph__mutmut_1': x_serialize_graph__mutmut_1, 
    'x_serialize_graph__mutmut_2': x_serialize_graph__mutmut_2, 
    'x_serialize_graph__mutmut_3': x_serialize_graph__mutmut_3, 
    'x_serialize_graph__mutmut_4': x_serialize_graph__mutmut_4, 
    'x_serialize_graph__mutmut_5': x_serialize_graph__mutmut_5, 
    'x_serialize_graph__mutmut_6': x_serialize_graph__mutmut_6
}
x_serialize_graph__mutmut_orig.__name__ = 'x_serialize_graph'


# =============================================================================
# PUBLIC EXPORT
# =============================================================================

__all__ = [
    "serialize_graph",
    "serialize_graph_payload",
]