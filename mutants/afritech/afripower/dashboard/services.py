"""
AFRIPower Dashboard Services

Read-only observational metric services.

This module MUST NEVER:
- execute runtime behavior
- validate truth
- enforce governance
- mutate receipts
- mutate proof artifacts
- create authority
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Dict, List, Tuple

from afritech.afripower.dashboard.constants import (
    DASHBOARD_STATUS,
    DISPLAY_ONLY,
    METRIC_CLASSIFICATION,
    OBSERVATIONAL_ONLY,
    READ_ONLY,
)


# =============================================================================
# TYPES
# =============================================================================

Receipt = Mapping[str, Any]
_TRACEABILITY_KEY = "governance_traceability"
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


def _safe_sequence(value: object) -> Tuple[Any, ...]:
    args = [value]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__safe_sequence__mutmut_orig, x__safe_sequence__mutmut_mutants, args, kwargs, None)


def x__safe_sequence__mutmut_orig(value: object) -> Tuple[Any, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(value)


def x__safe_sequence__mutmut_1(value: object) -> Tuple[Any, ...]:
    if not isinstance(value, Sequence) and isinstance(value, (str, bytes)):
        return ()
    return tuple(value)


def x__safe_sequence__mutmut_2(value: object) -> Tuple[Any, ...]:
    if isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(value)


def x__safe_sequence__mutmut_3(value: object) -> Tuple[Any, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(None)

x__safe_sequence__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__safe_sequence__mutmut_1': x__safe_sequence__mutmut_1, 
    'x__safe_sequence__mutmut_2': x__safe_sequence__mutmut_2, 
    'x__safe_sequence__mutmut_3': x__safe_sequence__mutmut_3
}
x__safe_sequence__mutmut_orig.__name__ = 'x__safe_sequence'


def _safe_traceability(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    args = [receipt]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__safe_traceability__mutmut_orig, x__safe_traceability__mutmut_mutants, args, kwargs, None)


def x__safe_traceability__mutmut_orig(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ Defensive filtering
    ✅ Deterministic
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))

    result: List[Mapping[str, Any]] = []
    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x__safe_traceability__mutmut_1(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ Defensive filtering
    ✅ Deterministic
    """

    raw = None

    result: List[Mapping[str, Any]] = []
    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x__safe_traceability__mutmut_2(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ Defensive filtering
    ✅ Deterministic
    """

    raw = _safe_sequence(None)

    result: List[Mapping[str, Any]] = []
    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x__safe_traceability__mutmut_3(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ Defensive filtering
    ✅ Deterministic
    """

    raw = _safe_sequence(receipt.get(None, ()))

    result: List[Mapping[str, Any]] = []
    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x__safe_traceability__mutmut_4(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ Defensive filtering
    ✅ Deterministic
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, None))

    result: List[Mapping[str, Any]] = []
    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x__safe_traceability__mutmut_5(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ Defensive filtering
    ✅ Deterministic
    """

    raw = _safe_sequence(receipt.get(()))

    result: List[Mapping[str, Any]] = []
    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x__safe_traceability__mutmut_6(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ Defensive filtering
    ✅ Deterministic
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ))

    result: List[Mapping[str, Any]] = []
    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x__safe_traceability__mutmut_7(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ Defensive filtering
    ✅ Deterministic
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))

    result: List[Mapping[str, Any]] = None
    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x__safe_traceability__mutmut_8(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ Defensive filtering
    ✅ Deterministic
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))

    result: List[Mapping[str, Any]] = []
    for item in raw:
        if isinstance(item, Mapping):
            result.append(None)

    return tuple(result)


def x__safe_traceability__mutmut_9(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ Defensive filtering
    ✅ Deterministic
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))

    result: List[Mapping[str, Any]] = []
    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(None)

x__safe_traceability__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__safe_traceability__mutmut_1': x__safe_traceability__mutmut_1, 
    'x__safe_traceability__mutmut_2': x__safe_traceability__mutmut_2, 
    'x__safe_traceability__mutmut_3': x__safe_traceability__mutmut_3, 
    'x__safe_traceability__mutmut_4': x__safe_traceability__mutmut_4, 
    'x__safe_traceability__mutmut_5': x__safe_traceability__mutmut_5, 
    'x__safe_traceability__mutmut_6': x__safe_traceability__mutmut_6, 
    'x__safe_traceability__mutmut_7': x__safe_traceability__mutmut_7, 
    'x__safe_traceability__mutmut_8': x__safe_traceability__mutmut_8, 
    'x__safe_traceability__mutmut_9': x__safe_traceability__mutmut_9
}
x__safe_traceability__mutmut_orig.__name__ = 'x__safe_traceability'


def _safe_execution_id(receipt: Receipt) -> str:
    args = [receipt]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__safe_execution_id__mutmut_orig, x__safe_execution_id__mutmut_mutants, args, kwargs, None)


def x__safe_execution_id__mutmut_orig(receipt: Receipt) -> str:
    return _safe_str(receipt.get("execution_id"))


def x__safe_execution_id__mutmut_1(receipt: Receipt) -> str:
    return _safe_str(None)


def x__safe_execution_id__mutmut_2(receipt: Receipt) -> str:
    return _safe_str(receipt.get(None))


def x__safe_execution_id__mutmut_3(receipt: Receipt) -> str:
    return _safe_str(receipt.get("XXexecution_idXX"))


def x__safe_execution_id__mutmut_4(receipt: Receipt) -> str:
    return _safe_str(receipt.get("EXECUTION_ID"))

x__safe_execution_id__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__safe_execution_id__mutmut_1': x__safe_execution_id__mutmut_1, 
    'x__safe_execution_id__mutmut_2': x__safe_execution_id__mutmut_2, 
    'x__safe_execution_id__mutmut_3': x__safe_execution_id__mutmut_3, 
    'x__safe_execution_id__mutmut_4': x__safe_execution_id__mutmut_4
}
x__safe_execution_id__mutmut_orig.__name__ = 'x__safe_execution_id'


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def compute_metrics(receipts: Iterable[Receipt]) -> Dict[str, object]:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_compute_metrics__mutmut_orig, x_compute_metrics__mutmut_mutants, args, kwargs, None)


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_orig(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_1(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = None

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_2(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = None

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_3(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(None)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_4(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(None)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_5(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = None

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_6(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(None)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_7(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = None

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_8(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(None)
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_9(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get(None))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_10(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("XXidXX"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_11(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("ID"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_12(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(None)
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_13(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get(None))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_14(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("XXidXX"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_15(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("ID"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_16(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = None
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_17(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = None

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_18(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = None

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_19(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs * total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_20(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 1.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_21(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "XXdashboard_statusXX": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_22(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "DASHBOARD_STATUS": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_23(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "XXmetric_classificationXX": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_24(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "METRIC_CLASSIFICATION": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_25(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "XXread_onlyXX": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_26(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "READ_ONLY": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_27(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "XXdisplay_onlyXX": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_28(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "DISPLAY_ONLY": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_29(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "XXobservational_onlyXX": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_30(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "OBSERVATIONAL_ONLY": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_31(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "XXtotal_receiptsXX": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_32(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "TOTAL_RECEIPTS": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_33(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "XXunique_execution_idsXX": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_34(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "UNIQUE_EXECUTION_IDS": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_35(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "XXtotal_governance_referencesXX": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_36(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "TOTAL_GOVERNANCE_REFERENCES": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_37(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "XXunique_governance_referencesXX": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_38(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "UNIQUE_GOVERNANCE_REFERENCES": len(unique_ref_ids),
        "avg_refs_per_execution": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_39(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "XXavg_refs_per_executionXX": avg_refs,
    }


# =============================================================================
# CORE METRIC COMPUTATION
# =============================================================================

def x_compute_metrics__mutmut_40(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Compute observational dashboard metrics.

    ✅ Read-only
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    execution_ids = {
        _safe_execution_id(r)
        for r in receipt_list
        if _safe_execution_id(r)
    }

    governance_refs: List[Mapping[str, Any]] = [
        ref
        for r in receipt_list
        for ref in _safe_traceability(r)
    ]

    unique_ref_ids = {
        _safe_str(ref.get("id"))
        for ref in governance_refs
        if _safe_str(ref.get("id"))
    }

    total_receipts = len(receipt_list)
    total_refs = len(governance_refs)

    avg_refs = total_refs / total_receipts if total_receipts else 0.0

    return {
        # status
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "total_receipts": total_receipts,
        "unique_execution_ids": len(execution_ids),
        "total_governance_references": total_refs,
        "unique_governance_references": len(unique_ref_ids),
        "AVG_REFS_PER_EXECUTION": avg_refs,
    }

x_compute_metrics__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_compute_metrics__mutmut_1': x_compute_metrics__mutmut_1, 
    'x_compute_metrics__mutmut_2': x_compute_metrics__mutmut_2, 
    'x_compute_metrics__mutmut_3': x_compute_metrics__mutmut_3, 
    'x_compute_metrics__mutmut_4': x_compute_metrics__mutmut_4, 
    'x_compute_metrics__mutmut_5': x_compute_metrics__mutmut_5, 
    'x_compute_metrics__mutmut_6': x_compute_metrics__mutmut_6, 
    'x_compute_metrics__mutmut_7': x_compute_metrics__mutmut_7, 
    'x_compute_metrics__mutmut_8': x_compute_metrics__mutmut_8, 
    'x_compute_metrics__mutmut_9': x_compute_metrics__mutmut_9, 
    'x_compute_metrics__mutmut_10': x_compute_metrics__mutmut_10, 
    'x_compute_metrics__mutmut_11': x_compute_metrics__mutmut_11, 
    'x_compute_metrics__mutmut_12': x_compute_metrics__mutmut_12, 
    'x_compute_metrics__mutmut_13': x_compute_metrics__mutmut_13, 
    'x_compute_metrics__mutmut_14': x_compute_metrics__mutmut_14, 
    'x_compute_metrics__mutmut_15': x_compute_metrics__mutmut_15, 
    'x_compute_metrics__mutmut_16': x_compute_metrics__mutmut_16, 
    'x_compute_metrics__mutmut_17': x_compute_metrics__mutmut_17, 
    'x_compute_metrics__mutmut_18': x_compute_metrics__mutmut_18, 
    'x_compute_metrics__mutmut_19': x_compute_metrics__mutmut_19, 
    'x_compute_metrics__mutmut_20': x_compute_metrics__mutmut_20, 
    'x_compute_metrics__mutmut_21': x_compute_metrics__mutmut_21, 
    'x_compute_metrics__mutmut_22': x_compute_metrics__mutmut_22, 
    'x_compute_metrics__mutmut_23': x_compute_metrics__mutmut_23, 
    'x_compute_metrics__mutmut_24': x_compute_metrics__mutmut_24, 
    'x_compute_metrics__mutmut_25': x_compute_metrics__mutmut_25, 
    'x_compute_metrics__mutmut_26': x_compute_metrics__mutmut_26, 
    'x_compute_metrics__mutmut_27': x_compute_metrics__mutmut_27, 
    'x_compute_metrics__mutmut_28': x_compute_metrics__mutmut_28, 
    'x_compute_metrics__mutmut_29': x_compute_metrics__mutmut_29, 
    'x_compute_metrics__mutmut_30': x_compute_metrics__mutmut_30, 
    'x_compute_metrics__mutmut_31': x_compute_metrics__mutmut_31, 
    'x_compute_metrics__mutmut_32': x_compute_metrics__mutmut_32, 
    'x_compute_metrics__mutmut_33': x_compute_metrics__mutmut_33, 
    'x_compute_metrics__mutmut_34': x_compute_metrics__mutmut_34, 
    'x_compute_metrics__mutmut_35': x_compute_metrics__mutmut_35, 
    'x_compute_metrics__mutmut_36': x_compute_metrics__mutmut_36, 
    'x_compute_metrics__mutmut_37': x_compute_metrics__mutmut_37, 
    'x_compute_metrics__mutmut_38': x_compute_metrics__mutmut_38, 
    'x_compute_metrics__mutmut_39': x_compute_metrics__mutmut_39, 
    'x_compute_metrics__mutmut_40': x_compute_metrics__mutmut_40
}
x_compute_metrics__mutmut_orig.__name__ = 'x_compute_metrics'


# =============================================================================
# DISTRIBUTION HELPERS
# =============================================================================

def _sorted_counter(counter: Counter[str]) -> Dict[str, int]:
    args = [counter]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__sorted_counter__mutmut_orig, x__sorted_counter__mutmut_mutants, args, kwargs, None)


# =============================================================================
# DISTRIBUTION HELPERS
# =============================================================================

def x__sorted_counter__mutmut_orig(counter: Counter[str]) -> Dict[str, int]:
    """
    Deterministic sorting:
        - descending frequency
        - lexicographic tie-break
    """
    return dict(
        sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


# =============================================================================
# DISTRIBUTION HELPERS
# =============================================================================

def x__sorted_counter__mutmut_1(counter: Counter[str]) -> Dict[str, int]:
    """
    Deterministic sorting:
        - descending frequency
        - lexicographic tie-break
    """
    return dict(
        None
    )


# =============================================================================
# DISTRIBUTION HELPERS
# =============================================================================

def x__sorted_counter__mutmut_2(counter: Counter[str]) -> Dict[str, int]:
    """
    Deterministic sorting:
        - descending frequency
        - lexicographic tie-break
    """
    return dict(
        sorted(None, key=lambda item: (-item[1], item[0]))
    )


# =============================================================================
# DISTRIBUTION HELPERS
# =============================================================================

def x__sorted_counter__mutmut_3(counter: Counter[str]) -> Dict[str, int]:
    """
    Deterministic sorting:
        - descending frequency
        - lexicographic tie-break
    """
    return dict(
        sorted(counter.items(), key=None)
    )


# =============================================================================
# DISTRIBUTION HELPERS
# =============================================================================

def x__sorted_counter__mutmut_4(counter: Counter[str]) -> Dict[str, int]:
    """
    Deterministic sorting:
        - descending frequency
        - lexicographic tie-break
    """
    return dict(
        sorted(key=lambda item: (-item[1], item[0]))
    )


# =============================================================================
# DISTRIBUTION HELPERS
# =============================================================================

def x__sorted_counter__mutmut_5(counter: Counter[str]) -> Dict[str, int]:
    """
    Deterministic sorting:
        - descending frequency
        - lexicographic tie-break
    """
    return dict(
        sorted(counter.items(), )
    )


# =============================================================================
# DISTRIBUTION HELPERS
# =============================================================================

def x__sorted_counter__mutmut_6(counter: Counter[str]) -> Dict[str, int]:
    """
    Deterministic sorting:
        - descending frequency
        - lexicographic tie-break
    """
    return dict(
        sorted(counter.items(), key=lambda item: None)
    )


# =============================================================================
# DISTRIBUTION HELPERS
# =============================================================================

def x__sorted_counter__mutmut_7(counter: Counter[str]) -> Dict[str, int]:
    """
    Deterministic sorting:
        - descending frequency
        - lexicographic tie-break
    """
    return dict(
        sorted(counter.items(), key=lambda item: (+item[1], item[0]))
    )


# =============================================================================
# DISTRIBUTION HELPERS
# =============================================================================

def x__sorted_counter__mutmut_8(counter: Counter[str]) -> Dict[str, int]:
    """
    Deterministic sorting:
        - descending frequency
        - lexicographic tie-break
    """
    return dict(
        sorted(counter.items(), key=lambda item: (-item[2], item[0]))
    )


# =============================================================================
# DISTRIBUTION HELPERS
# =============================================================================

def x__sorted_counter__mutmut_9(counter: Counter[str]) -> Dict[str, int]:
    """
    Deterministic sorting:
        - descending frequency
        - lexicographic tie-break
    """
    return dict(
        sorted(counter.items(), key=lambda item: (-item[1], item[1]))
    )

x__sorted_counter__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__sorted_counter__mutmut_1': x__sorted_counter__mutmut_1, 
    'x__sorted_counter__mutmut_2': x__sorted_counter__mutmut_2, 
    'x__sorted_counter__mutmut_3': x__sorted_counter__mutmut_3, 
    'x__sorted_counter__mutmut_4': x__sorted_counter__mutmut_4, 
    'x__sorted_counter__mutmut_5': x__sorted_counter__mutmut_5, 
    'x__sorted_counter__mutmut_6': x__sorted_counter__mutmut_6, 
    'x__sorted_counter__mutmut_7': x__sorted_counter__mutmut_7, 
    'x__sorted_counter__mutmut_8': x__sorted_counter__mutmut_8, 
    'x__sorted_counter__mutmut_9': x__sorted_counter__mutmut_9
}
x__sorted_counter__mutmut_orig.__name__ = 'x__sorted_counter'


def summarize_governance_reference_usage(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_summarize_governance_reference_usage__mutmut_orig, x_summarize_governance_reference_usage__mutmut_mutants, args, kwargs, None)


def x_summarize_governance_reference_usage__mutmut_orig(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference usage (IDs).

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_id = _safe_str(ref.get("id"))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_usage__mutmut_1(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference usage (IDs).

    ✅ Observational only
    """

    counter: Counter[str] = None

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_id = _safe_str(ref.get("id"))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_usage__mutmut_2(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference usage (IDs).

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_id = _safe_str(ref.get("id"))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_usage__mutmut_3(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference usage (IDs).

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            break

        for ref in _safe_traceability(receipt):
            ref_id = _safe_str(ref.get("id"))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_usage__mutmut_4(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference usage (IDs).

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(None):
            ref_id = _safe_str(ref.get("id"))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_usage__mutmut_5(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference usage (IDs).

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_id = None
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_usage__mutmut_6(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference usage (IDs).

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_id = _safe_str(None)
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_usage__mutmut_7(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference usage (IDs).

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_id = _safe_str(ref.get(None))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_usage__mutmut_8(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference usage (IDs).

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_id = _safe_str(ref.get("XXidXX"))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_usage__mutmut_9(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference usage (IDs).

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_id = _safe_str(ref.get("ID"))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_usage__mutmut_10(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference usage (IDs).

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_id = _safe_str(ref.get("id"))
            if ref_id:
                counter[ref_id] = 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_usage__mutmut_11(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference usage (IDs).

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_id = _safe_str(ref.get("id"))
            if ref_id:
                counter[ref_id] -= 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_usage__mutmut_12(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference usage (IDs).

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_id = _safe_str(ref.get("id"))
            if ref_id:
                counter[ref_id] += 2

    return _sorted_counter(counter)


def x_summarize_governance_reference_usage__mutmut_13(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference usage (IDs).

    ✅ Observational only
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_id = _safe_str(ref.get("id"))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(None)

x_summarize_governance_reference_usage__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_summarize_governance_reference_usage__mutmut_1': x_summarize_governance_reference_usage__mutmut_1, 
    'x_summarize_governance_reference_usage__mutmut_2': x_summarize_governance_reference_usage__mutmut_2, 
    'x_summarize_governance_reference_usage__mutmut_3': x_summarize_governance_reference_usage__mutmut_3, 
    'x_summarize_governance_reference_usage__mutmut_4': x_summarize_governance_reference_usage__mutmut_4, 
    'x_summarize_governance_reference_usage__mutmut_5': x_summarize_governance_reference_usage__mutmut_5, 
    'x_summarize_governance_reference_usage__mutmut_6': x_summarize_governance_reference_usage__mutmut_6, 
    'x_summarize_governance_reference_usage__mutmut_7': x_summarize_governance_reference_usage__mutmut_7, 
    'x_summarize_governance_reference_usage__mutmut_8': x_summarize_governance_reference_usage__mutmut_8, 
    'x_summarize_governance_reference_usage__mutmut_9': x_summarize_governance_reference_usage__mutmut_9, 
    'x_summarize_governance_reference_usage__mutmut_10': x_summarize_governance_reference_usage__mutmut_10, 
    'x_summarize_governance_reference_usage__mutmut_11': x_summarize_governance_reference_usage__mutmut_11, 
    'x_summarize_governance_reference_usage__mutmut_12': x_summarize_governance_reference_usage__mutmut_12, 
    'x_summarize_governance_reference_usage__mutmut_13': x_summarize_governance_reference_usage__mutmut_13
}
x_summarize_governance_reference_usage__mutmut_orig.__name__ = 'x_summarize_governance_reference_usage'


def summarize_governance_reference_type_usage(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_summarize_governance_reference_type_usage__mutmut_orig, x_summarize_governance_reference_type_usage__mutmut_mutants, args, kwargs, None)


def x_summarize_governance_reference_type_usage__mutmut_orig(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference type usage.
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_type = _safe_str(ref.get("type"))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_type_usage__mutmut_1(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference type usage.
    """

    counter: Counter[str] = None

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_type = _safe_str(ref.get("type"))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_type_usage__mutmut_2(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference type usage.
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_type = _safe_str(ref.get("type"))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_type_usage__mutmut_3(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference type usage.
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            break

        for ref in _safe_traceability(receipt):
            ref_type = _safe_str(ref.get("type"))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_type_usage__mutmut_4(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference type usage.
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(None):
            ref_type = _safe_str(ref.get("type"))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_type_usage__mutmut_5(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference type usage.
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_type = None
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_type_usage__mutmut_6(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference type usage.
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_type = _safe_str(None)
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_type_usage__mutmut_7(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference type usage.
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_type = _safe_str(ref.get(None))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_type_usage__mutmut_8(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference type usage.
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_type = _safe_str(ref.get("XXtypeXX"))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_type_usage__mutmut_9(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference type usage.
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_type = _safe_str(ref.get("TYPE"))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_type_usage__mutmut_10(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference type usage.
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_type = _safe_str(ref.get("type"))
            if ref_type:
                counter[ref_type] = 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_type_usage__mutmut_11(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference type usage.
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_type = _safe_str(ref.get("type"))
            if ref_type:
                counter[ref_type] -= 1

    return _sorted_counter(counter)


def x_summarize_governance_reference_type_usage__mutmut_12(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference type usage.
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_type = _safe_str(ref.get("type"))
            if ref_type:
                counter[ref_type] += 2

    return _sorted_counter(counter)


def x_summarize_governance_reference_type_usage__mutmut_13(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """
    Count governance reference type usage.
    """

    counter: Counter[str] = Counter()

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in _safe_traceability(receipt):
            ref_type = _safe_str(ref.get("type"))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(None)

x_summarize_governance_reference_type_usage__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_summarize_governance_reference_type_usage__mutmut_1': x_summarize_governance_reference_type_usage__mutmut_1, 
    'x_summarize_governance_reference_type_usage__mutmut_2': x_summarize_governance_reference_type_usage__mutmut_2, 
    'x_summarize_governance_reference_type_usage__mutmut_3': x_summarize_governance_reference_type_usage__mutmut_3, 
    'x_summarize_governance_reference_type_usage__mutmut_4': x_summarize_governance_reference_type_usage__mutmut_4, 
    'x_summarize_governance_reference_type_usage__mutmut_5': x_summarize_governance_reference_type_usage__mutmut_5, 
    'x_summarize_governance_reference_type_usage__mutmut_6': x_summarize_governance_reference_type_usage__mutmut_6, 
    'x_summarize_governance_reference_type_usage__mutmut_7': x_summarize_governance_reference_type_usage__mutmut_7, 
    'x_summarize_governance_reference_type_usage__mutmut_8': x_summarize_governance_reference_type_usage__mutmut_8, 
    'x_summarize_governance_reference_type_usage__mutmut_9': x_summarize_governance_reference_type_usage__mutmut_9, 
    'x_summarize_governance_reference_type_usage__mutmut_10': x_summarize_governance_reference_type_usage__mutmut_10, 
    'x_summarize_governance_reference_type_usage__mutmut_11': x_summarize_governance_reference_type_usage__mutmut_11, 
    'x_summarize_governance_reference_type_usage__mutmut_12': x_summarize_governance_reference_type_usage__mutmut_12, 
    'x_summarize_governance_reference_type_usage__mutmut_13': x_summarize_governance_reference_type_usage__mutmut_13
}
x_summarize_governance_reference_type_usage__mutmut_orig.__name__ = 'x_summarize_governance_reference_type_usage'


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def build_dashboard_payload(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_dashboard_payload__mutmut_orig, x_build_dashboard_payload__mutmut_mutants, args, kwargs, None)


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_orig(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_1(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = None

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_2(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "XXstatusXX": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_3(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "STATUS": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_4(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "XXREAD_ONLYXX",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_5(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "read_only",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_6(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "XXdashboard_statusXX": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_7(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "DASHBOARD_STATUS": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_8(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "XXread_onlyXX": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_9(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "READ_ONLY": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_10(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "XXdisplay_onlyXX": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_11(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "DISPLAY_ONLY": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_12(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "XXobservational_onlyXX": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_13(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "OBSERVATIONAL_ONLY": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_14(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "XXmetricsXX": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_15(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "METRICS": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_16(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(None),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_17(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "XXgovernance_reference_usageXX": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_18(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "GOVERNANCE_REFERENCE_USAGE": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_19(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            None
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_20(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "XXgovernance_reference_type_usageXX": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_21(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "GOVERNANCE_REFERENCE_TYPE_USAGE": summarize_governance_reference_type_usage(
            receipt_list
        ),
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_dashboard_payload__mutmut_22(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build complete AFRIPower dashboard payload.

    ✅ Pure
    ✅ Deterministic
    ✅ Safe for APIs / UI
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # core metrics
        "metrics": compute_metrics(receipt_list),

        # distributions
        "governance_reference_usage": summarize_governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": summarize_governance_reference_type_usage(
            None
        ),
    }

x_build_dashboard_payload__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_dashboard_payload__mutmut_1': x_build_dashboard_payload__mutmut_1, 
    'x_build_dashboard_payload__mutmut_2': x_build_dashboard_payload__mutmut_2, 
    'x_build_dashboard_payload__mutmut_3': x_build_dashboard_payload__mutmut_3, 
    'x_build_dashboard_payload__mutmut_4': x_build_dashboard_payload__mutmut_4, 
    'x_build_dashboard_payload__mutmut_5': x_build_dashboard_payload__mutmut_5, 
    'x_build_dashboard_payload__mutmut_6': x_build_dashboard_payload__mutmut_6, 
    'x_build_dashboard_payload__mutmut_7': x_build_dashboard_payload__mutmut_7, 
    'x_build_dashboard_payload__mutmut_8': x_build_dashboard_payload__mutmut_8, 
    'x_build_dashboard_payload__mutmut_9': x_build_dashboard_payload__mutmut_9, 
    'x_build_dashboard_payload__mutmut_10': x_build_dashboard_payload__mutmut_10, 
    'x_build_dashboard_payload__mutmut_11': x_build_dashboard_payload__mutmut_11, 
    'x_build_dashboard_payload__mutmut_12': x_build_dashboard_payload__mutmut_12, 
    'x_build_dashboard_payload__mutmut_13': x_build_dashboard_payload__mutmut_13, 
    'x_build_dashboard_payload__mutmut_14': x_build_dashboard_payload__mutmut_14, 
    'x_build_dashboard_payload__mutmut_15': x_build_dashboard_payload__mutmut_15, 
    'x_build_dashboard_payload__mutmut_16': x_build_dashboard_payload__mutmut_16, 
    'x_build_dashboard_payload__mutmut_17': x_build_dashboard_payload__mutmut_17, 
    'x_build_dashboard_payload__mutmut_18': x_build_dashboard_payload__mutmut_18, 
    'x_build_dashboard_payload__mutmut_19': x_build_dashboard_payload__mutmut_19, 
    'x_build_dashboard_payload__mutmut_20': x_build_dashboard_payload__mutmut_20, 
    'x_build_dashboard_payload__mutmut_21': x_build_dashboard_payload__mutmut_21, 
    'x_build_dashboard_payload__mutmut_22': x_build_dashboard_payload__mutmut_22
}
x_build_dashboard_payload__mutmut_orig.__name__ = 'x_build_dashboard_payload'


# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    "compute_metrics",
    "summarize_governance_reference_usage",
    "summarize_governance_reference_type_usage",
    "build_dashboard_payload",
]
