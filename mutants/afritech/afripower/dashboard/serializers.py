"""
AFRIPower Dashboard Serializers

Read-only serializers for observational dashboard payloads.

This module MUST NEVER:
- validate runtime truth
- enforce governance
- mutate receipts
- mutate proof artifacts
- create authority

This module is:
✅ serialization-only
✅ display-only
✅ non-authoritative
"""

from __future__ import annotations
from typing import Any, Dict

# -----------------------------------------------------------------------------
# Optional DRF import (safe fallback)
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
# NON-DRF FALLBACK (PURE PYTHON SERIALIZATION)
# =============================================================================

def serialize_dashboard_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    args = [payload]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_serialize_dashboard_payload__mutmut_orig, x_serialize_dashboard_payload__mutmut_mutants, args, kwargs, None)


# =============================================================================
# NON-DRF FALLBACK (PURE PYTHON SERIALIZATION)
# =============================================================================

def x_serialize_dashboard_payload__mutmut_orig(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pure fallback serializer when DRF is unavailable.

    ✅ No validation
    ✅ No mutation
    ✅ Pass-through (safe copy)
    """

    if not isinstance(payload, dict):
        return {}

    return dict(payload)


# =============================================================================
# NON-DRF FALLBACK (PURE PYTHON SERIALIZATION)
# =============================================================================

def x_serialize_dashboard_payload__mutmut_1(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pure fallback serializer when DRF is unavailable.

    ✅ No validation
    ✅ No mutation
    ✅ Pass-through (safe copy)
    """

    if isinstance(payload, dict):
        return {}

    return dict(payload)


# =============================================================================
# NON-DRF FALLBACK (PURE PYTHON SERIALIZATION)
# =============================================================================

def x_serialize_dashboard_payload__mutmut_2(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pure fallback serializer when DRF is unavailable.

    ✅ No validation
    ✅ No mutation
    ✅ Pass-through (safe copy)
    """

    if not isinstance(payload, dict):
        return {}

    return dict(None)

x_serialize_dashboard_payload__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_serialize_dashboard_payload__mutmut_1': x_serialize_dashboard_payload__mutmut_1, 
    'x_serialize_dashboard_payload__mutmut_2': x_serialize_dashboard_payload__mutmut_2
}
x_serialize_dashboard_payload__mutmut_orig.__name__ = 'x_serialize_dashboard_payload'


# =============================================================================
# DRF SERIALIZERS (READ-ONLY)
# =============================================================================

if serializers is not None:

    # -------------------------------------------------------------------------
    # Metric Summary Serializer
    # -------------------------------------------------------------------------

    class DashboardMetricSummarySerializer(serializers.Serializer):
        """
        Read-only metric summary serializer.

        ❗ No validation authority
        """

        dashboard_status = serializers.CharField(read_only=True)
        metric_classification = serializers.CharField(read_only=True)

        read_only = serializers.BooleanField(read_only=True)
        display_only = serializers.BooleanField(read_only=True)
        observational_only = serializers.BooleanField(read_only=True)

        total_receipts = serializers.IntegerField(read_only=True)
        unique_execution_ids = serializers.IntegerField(read_only=True)
        total_governance_references = serializers.IntegerField(read_only=True)
        unique_governance_references = serializers.IntegerField(read_only=True)
        avg_refs_per_execution = serializers.FloatField(read_only=True)


    # -------------------------------------------------------------------------
    # Main Dashboard Payload
    # -------------------------------------------------------------------------

    class DashboardPayloadSerializer(serializers.Serializer):
        """
        Full dashboard payload serializer.

        ✅ Read-only
        ✅ Non-authoritative
        ✅ Display-safe
        """

        status = serializers.CharField(read_only=True)
        dashboard_status = serializers.CharField(read_only=True)

        read_only = serializers.BooleanField(read_only=True)
        display_only = serializers.BooleanField(read_only=True)
        observational_only = serializers.BooleanField(read_only=True)

        # Explicit authority flags (must remain False upstream)
        runtime_authority = serializers.BooleanField(read_only=True)
        validation_authority = serializers.BooleanField(read_only=True)
        governance_authority = serializers.BooleanField(read_only=True)
        enforcement_authority = serializers.BooleanField(read_only=True)

        metrics = DashboardMetricSummarySerializer(read_only=True)

        governance_reference_usage = serializers.DictField(
            child=serializers.IntegerField(),
            read_only=True,
        )

        governance_reference_type_usage = serializers.DictField(
            child=serializers.IntegerField(),
            read_only=True,
        )


    # -------------------------------------------------------------------------
    # Serializer Helpers
    # -------------------------------------------------------------------------

    def serialize_with_drf(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply DRF serialization safely.

        ✅ No validation enforcement
        ✅ Read-only representation
        """

        serializer = DashboardPayloadSerializer(payload)
        return serializer.data


else:
    # -------------------------------------------------------------------------
    # Fallback when DRF is unavailable
    # -------------------------------------------------------------------------

    DashboardMetricSummarySerializer = None  # type: ignore
    DashboardPayloadSerializer = None  # type: ignore

    def serialize_with_drf(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback serializer.

        ✅ Safe pass-through
        """
        return serialize_dashboard_payload(payload)


# =============================================================================
# UNIFIED PUBLIC SERIALIZER
# =============================================================================

def serialize_dashboard(
    payload: Dict[str, Any],
    use_drf: bool = True,
) -> Dict[str, Any]:
    args = [payload, use_drf]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_serialize_dashboard__mutmut_orig, x_serialize_dashboard__mutmut_mutants, args, kwargs, None)


# =============================================================================
# UNIFIED PUBLIC SERIALIZER
# =============================================================================

def x_serialize_dashboard__mutmut_orig(
    payload: Dict[str, Any],
    use_drf: bool = True,
) -> Dict[str, Any]:
    """
    Unified serializer entry point.

    ✅ Safe for API usage
    ✅ Compatible with/without DRF
    ✅ No authority or validation logic
    """

    if not isinstance(payload, dict):
        return {}

    if use_drf and serializers is not None:
        return serialize_with_drf(payload)

    return serialize_dashboard_payload(payload)


# =============================================================================
# UNIFIED PUBLIC SERIALIZER
# =============================================================================

def x_serialize_dashboard__mutmut_1(
    payload: Dict[str, Any],
    use_drf: bool = False,
) -> Dict[str, Any]:
    """
    Unified serializer entry point.

    ✅ Safe for API usage
    ✅ Compatible with/without DRF
    ✅ No authority or validation logic
    """

    if not isinstance(payload, dict):
        return {}

    if use_drf and serializers is not None:
        return serialize_with_drf(payload)

    return serialize_dashboard_payload(payload)


# =============================================================================
# UNIFIED PUBLIC SERIALIZER
# =============================================================================

def x_serialize_dashboard__mutmut_2(
    payload: Dict[str, Any],
    use_drf: bool = True,
) -> Dict[str, Any]:
    """
    Unified serializer entry point.

    ✅ Safe for API usage
    ✅ Compatible with/without DRF
    ✅ No authority or validation logic
    """

    if isinstance(payload, dict):
        return {}

    if use_drf and serializers is not None:
        return serialize_with_drf(payload)

    return serialize_dashboard_payload(payload)


# =============================================================================
# UNIFIED PUBLIC SERIALIZER
# =============================================================================

def x_serialize_dashboard__mutmut_3(
    payload: Dict[str, Any],
    use_drf: bool = True,
) -> Dict[str, Any]:
    """
    Unified serializer entry point.

    ✅ Safe for API usage
    ✅ Compatible with/without DRF
    ✅ No authority or validation logic
    """

    if not isinstance(payload, dict):
        return {}

    if use_drf or serializers is not None:
        return serialize_with_drf(payload)

    return serialize_dashboard_payload(payload)


# =============================================================================
# UNIFIED PUBLIC SERIALIZER
# =============================================================================

def x_serialize_dashboard__mutmut_4(
    payload: Dict[str, Any],
    use_drf: bool = True,
) -> Dict[str, Any]:
    """
    Unified serializer entry point.

    ✅ Safe for API usage
    ✅ Compatible with/without DRF
    ✅ No authority or validation logic
    """

    if not isinstance(payload, dict):
        return {}

    if use_drf and serializers is None:
        return serialize_with_drf(payload)

    return serialize_dashboard_payload(payload)


# =============================================================================
# UNIFIED PUBLIC SERIALIZER
# =============================================================================

def x_serialize_dashboard__mutmut_5(
    payload: Dict[str, Any],
    use_drf: bool = True,
) -> Dict[str, Any]:
    """
    Unified serializer entry point.

    ✅ Safe for API usage
    ✅ Compatible with/without DRF
    ✅ No authority or validation logic
    """

    if not isinstance(payload, dict):
        return {}

    if use_drf and serializers is not None:
        return serialize_with_drf(None)

    return serialize_dashboard_payload(payload)


# =============================================================================
# UNIFIED PUBLIC SERIALIZER
# =============================================================================

def x_serialize_dashboard__mutmut_6(
    payload: Dict[str, Any],
    use_drf: bool = True,
) -> Dict[str, Any]:
    """
    Unified serializer entry point.

    ✅ Safe for API usage
    ✅ Compatible with/without DRF
    ✅ No authority or validation logic
    """

    if not isinstance(payload, dict):
        return {}

    if use_drf and serializers is not None:
        return serialize_with_drf(payload)

    return serialize_dashboard_payload(None)

x_serialize_dashboard__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_serialize_dashboard__mutmut_1': x_serialize_dashboard__mutmut_1, 
    'x_serialize_dashboard__mutmut_2': x_serialize_dashboard__mutmut_2, 
    'x_serialize_dashboard__mutmut_3': x_serialize_dashboard__mutmut_3, 
    'x_serialize_dashboard__mutmut_4': x_serialize_dashboard__mutmut_4, 
    'x_serialize_dashboard__mutmut_5': x_serialize_dashboard__mutmut_5, 
    'x_serialize_dashboard__mutmut_6': x_serialize_dashboard__mutmut_6
}
x_serialize_dashboard__mutmut_orig.__name__ = 'x_serialize_dashboard'


# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    "serialize_dashboard",
    "serialize_dashboard_payload",
]
