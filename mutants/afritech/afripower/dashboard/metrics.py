"""
AFRIPower Dashboard Metrics

Pure read-only metric helpers.

This module MUST NEVER:
- execute runtime behavior
- validate truth
- enforce governance
- mutate receipts
- mutate proof artifacts
- create authority

This module is:
✅ observational
✅ read-only
✅ non-authoritative
✅ deterministic
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

MetricValue = int | float | str | bool
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


# =============================================================================
# EXTRACTION
# =============================================================================

def safe_traceability(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    args = [receipt]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_safe_traceability__mutmut_orig, x_safe_traceability__mutmut_mutants, args, kwargs, None)


# =============================================================================
# EXTRACTION
# =============================================================================

def x_safe_traceability__mutmut_orig(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ Defensive filtering
    ✅ Deterministic
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, []))

    result: List[Mapping[str, Any]] = []

    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


# =============================================================================
# EXTRACTION
# =============================================================================

def x_safe_traceability__mutmut_1(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
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


# =============================================================================
# EXTRACTION
# =============================================================================

def x_safe_traceability__mutmut_2(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
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


# =============================================================================
# EXTRACTION
# =============================================================================

def x_safe_traceability__mutmut_3(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ Defensive filtering
    ✅ Deterministic
    """

    raw = _safe_sequence(receipt.get(None, []))

    result: List[Mapping[str, Any]] = []

    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


# =============================================================================
# EXTRACTION
# =============================================================================

def x_safe_traceability__mutmut_4(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
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


# =============================================================================
# EXTRACTION
# =============================================================================

def x_safe_traceability__mutmut_5(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ Defensive filtering
    ✅ Deterministic
    """

    raw = _safe_sequence(receipt.get([]))

    result: List[Mapping[str, Any]] = []

    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


# =============================================================================
# EXTRACTION
# =============================================================================

def x_safe_traceability__mutmut_6(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
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


# =============================================================================
# EXTRACTION
# =============================================================================

def x_safe_traceability__mutmut_7(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ Defensive filtering
    ✅ Deterministic
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, []))

    result: List[Mapping[str, Any]] = None

    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


# =============================================================================
# EXTRACTION
# =============================================================================

def x_safe_traceability__mutmut_8(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ Defensive filtering
    ✅ Deterministic
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, []))

    result: List[Mapping[str, Any]] = []

    for item in raw:
        if isinstance(item, Mapping):
            result.append(None)

    return tuple(result)


# =============================================================================
# EXTRACTION
# =============================================================================

def x_safe_traceability__mutmut_9(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ Defensive filtering
    ✅ Deterministic
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, []))

    result: List[Mapping[str, Any]] = []

    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(None)

x_safe_traceability__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_safe_traceability__mutmut_1': x_safe_traceability__mutmut_1, 
    'x_safe_traceability__mutmut_2': x_safe_traceability__mutmut_2, 
    'x_safe_traceability__mutmut_3': x_safe_traceability__mutmut_3, 
    'x_safe_traceability__mutmut_4': x_safe_traceability__mutmut_4, 
    'x_safe_traceability__mutmut_5': x_safe_traceability__mutmut_5, 
    'x_safe_traceability__mutmut_6': x_safe_traceability__mutmut_6, 
    'x_safe_traceability__mutmut_7': x_safe_traceability__mutmut_7, 
    'x_safe_traceability__mutmut_8': x_safe_traceability__mutmut_8, 
    'x_safe_traceability__mutmut_9': x_safe_traceability__mutmut_9
}
x_safe_traceability__mutmut_orig.__name__ = 'x_safe_traceability'


def safe_execution_id(receipt: Receipt) -> str:
    args = [receipt]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_safe_execution_id__mutmut_orig, x_safe_execution_id__mutmut_mutants, args, kwargs, None)


def x_safe_execution_id__mutmut_orig(receipt: Receipt) -> str:
    """Return valid execution ID."""

    return _safe_str(receipt.get("execution_id"))


def x_safe_execution_id__mutmut_1(receipt: Receipt) -> str:
    """Return valid execution ID."""

    return _safe_str(None)


def x_safe_execution_id__mutmut_2(receipt: Receipt) -> str:
    """Return valid execution ID."""

    return _safe_str(receipt.get(None))


def x_safe_execution_id__mutmut_3(receipt: Receipt) -> str:
    """Return valid execution ID."""

    return _safe_str(receipt.get("XXexecution_idXX"))


def x_safe_execution_id__mutmut_4(receipt: Receipt) -> str:
    """Return valid execution ID."""

    return _safe_str(receipt.get("EXECUTION_ID"))

x_safe_execution_id__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_safe_execution_id__mutmut_1': x_safe_execution_id__mutmut_1, 
    'x_safe_execution_id__mutmut_2': x_safe_execution_id__mutmut_2, 
    'x_safe_execution_id__mutmut_3': x_safe_execution_id__mutmut_3, 
    'x_safe_execution_id__mutmut_4': x_safe_execution_id__mutmut_4
}
x_safe_execution_id__mutmut_orig.__name__ = 'x_safe_execution_id'


# =============================================================================
# BASIC METRICS
# =============================================================================

def count_receipts(receipts: Iterable[Receipt]) -> int:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_count_receipts__mutmut_orig, x_count_receipts__mutmut_mutants, args, kwargs, None)


# =============================================================================
# BASIC METRICS
# =============================================================================

def x_count_receipts__mutmut_orig(receipts: Iterable[Receipt]) -> int:
    """Count valid receipt records."""

    return sum(1 for r in receipts if isinstance(r, Mapping))


# =============================================================================
# BASIC METRICS
# =============================================================================

def x_count_receipts__mutmut_1(receipts: Iterable[Receipt]) -> int:
    """Count valid receipt records."""

    return sum(None)


# =============================================================================
# BASIC METRICS
# =============================================================================

def x_count_receipts__mutmut_2(receipts: Iterable[Receipt]) -> int:
    """Count valid receipt records."""

    return sum(2 for r in receipts if isinstance(r, Mapping))

x_count_receipts__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_count_receipts__mutmut_1': x_count_receipts__mutmut_1, 
    'x_count_receipts__mutmut_2': x_count_receipts__mutmut_2
}
x_count_receipts__mutmut_orig.__name__ = 'x_count_receipts'


def count_unique_execution_ids(receipts: Iterable[Receipt]) -> int:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_count_unique_execution_ids__mutmut_orig, x_count_unique_execution_ids__mutmut_mutants, args, kwargs, None)


def x_count_unique_execution_ids__mutmut_orig(receipts: Iterable[Receipt]) -> int:
    """Count unique execution IDs."""

    unique = {
        safe_execution_id(r)
        for r in receipts
        if safe_execution_id(r)
    }
    return len(unique)


def x_count_unique_execution_ids__mutmut_1(receipts: Iterable[Receipt]) -> int:
    """Count unique execution IDs."""

    unique = None
    return len(unique)


def x_count_unique_execution_ids__mutmut_2(receipts: Iterable[Receipt]) -> int:
    """Count unique execution IDs."""

    unique = {
        safe_execution_id(None)
        for r in receipts
        if safe_execution_id(r)
    }
    return len(unique)


def x_count_unique_execution_ids__mutmut_3(receipts: Iterable[Receipt]) -> int:
    """Count unique execution IDs."""

    unique = {
        safe_execution_id(r)
        for r in receipts
        if safe_execution_id(None)
    }
    return len(unique)

x_count_unique_execution_ids__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_count_unique_execution_ids__mutmut_1': x_count_unique_execution_ids__mutmut_1, 
    'x_count_unique_execution_ids__mutmut_2': x_count_unique_execution_ids__mutmut_2, 
    'x_count_unique_execution_ids__mutmut_3': x_count_unique_execution_ids__mutmut_3
}
x_count_unique_execution_ids__mutmut_orig.__name__ = 'x_count_unique_execution_ids'


# =============================================================================
# GOVERNANCE METRICS
# =============================================================================

def count_total_governance_references(receipts: Iterable[Receipt]) -> int:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_count_total_governance_references__mutmut_orig, x_count_total_governance_references__mutmut_mutants, args, kwargs, None)


# =============================================================================
# GOVERNANCE METRICS
# =============================================================================

def x_count_total_governance_references__mutmut_orig(receipts: Iterable[Receipt]) -> int:
    """Count total governance references."""

    return sum(
        len(safe_traceability(r))
        for r in receipts
        if isinstance(r, Mapping)
    )


# =============================================================================
# GOVERNANCE METRICS
# =============================================================================

def x_count_total_governance_references__mutmut_1(receipts: Iterable[Receipt]) -> int:
    """Count total governance references."""

    return sum(
        None
    )

x_count_total_governance_references__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_count_total_governance_references__mutmut_1': x_count_total_governance_references__mutmut_1
}
x_count_total_governance_references__mutmut_orig.__name__ = 'x_count_total_governance_references'


def count_unique_governance_references(receipts: Iterable[Receipt]) -> int:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_count_unique_governance_references__mutmut_orig, x_count_unique_governance_references__mutmut_mutants, args, kwargs, None)


def x_count_unique_governance_references__mutmut_orig(receipts: Iterable[Receipt]) -> int:
    """Count unique governance reference IDs."""

    unique = {
        ref_id
        for r in receipts
        for item in safe_traceability(r)
        if (ref_id := _safe_str(item.get("id")))
    }
    return len(unique)


def x_count_unique_governance_references__mutmut_1(receipts: Iterable[Receipt]) -> int:
    """Count unique governance reference IDs."""

    unique = None
    return len(unique)


def x_count_unique_governance_references__mutmut_2(receipts: Iterable[Receipt]) -> int:
    """Count unique governance reference IDs."""

    unique = {
        ref_id
        for r in receipts
        for item in safe_traceability(None)
        if (ref_id := _safe_str(item.get("id")))
    }
    return len(unique)


def x_count_unique_governance_references__mutmut_3(receipts: Iterable[Receipt]) -> int:
    """Count unique governance reference IDs."""

    unique = {
        ref_id
        for r in receipts
        for item in safe_traceability(r)
        if (ref_id := _safe_str(None))
    }
    return len(unique)


def x_count_unique_governance_references__mutmut_4(receipts: Iterable[Receipt]) -> int:
    """Count unique governance reference IDs."""

    unique = {
        ref_id
        for r in receipts
        for item in safe_traceability(r)
        if (ref_id := _safe_str(item.get(None)))
    }
    return len(unique)


def x_count_unique_governance_references__mutmut_5(receipts: Iterable[Receipt]) -> int:
    """Count unique governance reference IDs."""

    unique = {
        ref_id
        for r in receipts
        for item in safe_traceability(r)
        if (ref_id := _safe_str(item.get("XXidXX")))
    }
    return len(unique)


def x_count_unique_governance_references__mutmut_6(receipts: Iterable[Receipt]) -> int:
    """Count unique governance reference IDs."""

    unique = {
        ref_id
        for r in receipts
        for item in safe_traceability(r)
        if (ref_id := _safe_str(item.get("ID")))
    }
    return len(unique)

x_count_unique_governance_references__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_count_unique_governance_references__mutmut_1': x_count_unique_governance_references__mutmut_1, 
    'x_count_unique_governance_references__mutmut_2': x_count_unique_governance_references__mutmut_2, 
    'x_count_unique_governance_references__mutmut_3': x_count_unique_governance_references__mutmut_3, 
    'x_count_unique_governance_references__mutmut_4': x_count_unique_governance_references__mutmut_4, 
    'x_count_unique_governance_references__mutmut_5': x_count_unique_governance_references__mutmut_5, 
    'x_count_unique_governance_references__mutmut_6': x_count_unique_governance_references__mutmut_6
}
x_count_unique_governance_references__mutmut_orig.__name__ = 'x_count_unique_governance_references'


def average_references_per_execution(receipts: Iterable[Receipt]) -> float:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_average_references_per_execution__mutmut_orig, x_average_references_per_execution__mutmut_mutants, args, kwargs, None)


def x_average_references_per_execution__mutmut_orig(receipts: Iterable[Receipt]) -> float:
    """Compute average references per execution."""

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    if not receipt_list:
        return 0.0

    total_refs = count_total_governance_references(receipt_list)
    return total_refs / len(receipt_list)


def x_average_references_per_execution__mutmut_1(receipts: Iterable[Receipt]) -> float:
    """Compute average references per execution."""

    receipt_list = None

    if not receipt_list:
        return 0.0

    total_refs = count_total_governance_references(receipt_list)
    return total_refs / len(receipt_list)


def x_average_references_per_execution__mutmut_2(receipts: Iterable[Receipt]) -> float:
    """Compute average references per execution."""

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    if receipt_list:
        return 0.0

    total_refs = count_total_governance_references(receipt_list)
    return total_refs / len(receipt_list)


def x_average_references_per_execution__mutmut_3(receipts: Iterable[Receipt]) -> float:
    """Compute average references per execution."""

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    if not receipt_list:
        return 1.0

    total_refs = count_total_governance_references(receipt_list)
    return total_refs / len(receipt_list)


def x_average_references_per_execution__mutmut_4(receipts: Iterable[Receipt]) -> float:
    """Compute average references per execution."""

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    if not receipt_list:
        return 0.0

    total_refs = None
    return total_refs / len(receipt_list)


def x_average_references_per_execution__mutmut_5(receipts: Iterable[Receipt]) -> float:
    """Compute average references per execution."""

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    if not receipt_list:
        return 0.0

    total_refs = count_total_governance_references(None)
    return total_refs / len(receipt_list)


def x_average_references_per_execution__mutmut_6(receipts: Iterable[Receipt]) -> float:
    """Compute average references per execution."""

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    if not receipt_list:
        return 0.0

    total_refs = count_total_governance_references(receipt_list)
    return total_refs * len(receipt_list)

x_average_references_per_execution__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_average_references_per_execution__mutmut_1': x_average_references_per_execution__mutmut_1, 
    'x_average_references_per_execution__mutmut_2': x_average_references_per_execution__mutmut_2, 
    'x_average_references_per_execution__mutmut_3': x_average_references_per_execution__mutmut_3, 
    'x_average_references_per_execution__mutmut_4': x_average_references_per_execution__mutmut_4, 
    'x_average_references_per_execution__mutmut_5': x_average_references_per_execution__mutmut_5, 
    'x_average_references_per_execution__mutmut_6': x_average_references_per_execution__mutmut_6
}
x_average_references_per_execution__mutmut_orig.__name__ = 'x_average_references_per_execution'


# =============================================================================
# DISTRIBUTION METRICS
# =============================================================================

def _sorted_counter(counter: Counter) -> Dict[str, int]:
    args = [counter]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__sorted_counter__mutmut_orig, x__sorted_counter__mutmut_mutants, args, kwargs, None)


# =============================================================================
# DISTRIBUTION METRICS
# =============================================================================

def x__sorted_counter__mutmut_orig(counter: Counter) -> Dict[str, int]:
    """Deterministic sorting (descending, then key)."""
    return dict(
        sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


# =============================================================================
# DISTRIBUTION METRICS
# =============================================================================

def x__sorted_counter__mutmut_1(counter: Counter) -> Dict[str, int]:
    """Deterministic sorting (descending, then key)."""
    return dict(
        None
    )


# =============================================================================
# DISTRIBUTION METRICS
# =============================================================================

def x__sorted_counter__mutmut_2(counter: Counter) -> Dict[str, int]:
    """Deterministic sorting (descending, then key)."""
    return dict(
        sorted(None, key=lambda item: (-item[1], item[0]))
    )


# =============================================================================
# DISTRIBUTION METRICS
# =============================================================================

def x__sorted_counter__mutmut_3(counter: Counter) -> Dict[str, int]:
    """Deterministic sorting (descending, then key)."""
    return dict(
        sorted(counter.items(), key=None)
    )


# =============================================================================
# DISTRIBUTION METRICS
# =============================================================================

def x__sorted_counter__mutmut_4(counter: Counter) -> Dict[str, int]:
    """Deterministic sorting (descending, then key)."""
    return dict(
        sorted(key=lambda item: (-item[1], item[0]))
    )


# =============================================================================
# DISTRIBUTION METRICS
# =============================================================================

def x__sorted_counter__mutmut_5(counter: Counter) -> Dict[str, int]:
    """Deterministic sorting (descending, then key)."""
    return dict(
        sorted(counter.items(), )
    )


# =============================================================================
# DISTRIBUTION METRICS
# =============================================================================

def x__sorted_counter__mutmut_6(counter: Counter) -> Dict[str, int]:
    """Deterministic sorting (descending, then key)."""
    return dict(
        sorted(counter.items(), key=lambda item: None)
    )


# =============================================================================
# DISTRIBUTION METRICS
# =============================================================================

def x__sorted_counter__mutmut_7(counter: Counter) -> Dict[str, int]:
    """Deterministic sorting (descending, then key)."""
    return dict(
        sorted(counter.items(), key=lambda item: (+item[1], item[0]))
    )


# =============================================================================
# DISTRIBUTION METRICS
# =============================================================================

def x__sorted_counter__mutmut_8(counter: Counter) -> Dict[str, int]:
    """Deterministic sorting (descending, then key)."""
    return dict(
        sorted(counter.items(), key=lambda item: (-item[2], item[0]))
    )


# =============================================================================
# DISTRIBUTION METRICS
# =============================================================================

def x__sorted_counter__mutmut_9(counter: Counter) -> Dict[str, int]:
    """Deterministic sorting (descending, then key)."""
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


def governance_reference_usage(receipts: Iterable[Receipt]) -> Dict[str, int]:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_governance_reference_usage__mutmut_orig, x_governance_reference_usage__mutmut_mutants, args, kwargs, None)


def x_governance_reference_usage__mutmut_orig(receipts: Iterable[Receipt]) -> Dict[str, int]:
    """Count usage of governance reference IDs."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_id = _safe_str(item.get("id"))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_governance_reference_usage__mutmut_1(receipts: Iterable[Receipt]) -> Dict[str, int]:
    """Count usage of governance reference IDs."""

    counter: Counter[str] = None

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_id = _safe_str(item.get("id"))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_governance_reference_usage__mutmut_2(receipts: Iterable[Receipt]) -> Dict[str, int]:
    """Count usage of governance reference IDs."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_id = _safe_str(item.get("id"))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_governance_reference_usage__mutmut_3(receipts: Iterable[Receipt]) -> Dict[str, int]:
    """Count usage of governance reference IDs."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            break

        for item in safe_traceability(r):
            ref_id = _safe_str(item.get("id"))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_governance_reference_usage__mutmut_4(receipts: Iterable[Receipt]) -> Dict[str, int]:
    """Count usage of governance reference IDs."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(None):
            ref_id = _safe_str(item.get("id"))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_governance_reference_usage__mutmut_5(receipts: Iterable[Receipt]) -> Dict[str, int]:
    """Count usage of governance reference IDs."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_id = None
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_governance_reference_usage__mutmut_6(receipts: Iterable[Receipt]) -> Dict[str, int]:
    """Count usage of governance reference IDs."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_id = _safe_str(None)
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_governance_reference_usage__mutmut_7(receipts: Iterable[Receipt]) -> Dict[str, int]:
    """Count usage of governance reference IDs."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_id = _safe_str(item.get(None))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_governance_reference_usage__mutmut_8(receipts: Iterable[Receipt]) -> Dict[str, int]:
    """Count usage of governance reference IDs."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_id = _safe_str(item.get("XXidXX"))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_governance_reference_usage__mutmut_9(receipts: Iterable[Receipt]) -> Dict[str, int]:
    """Count usage of governance reference IDs."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_id = _safe_str(item.get("ID"))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(counter)


def x_governance_reference_usage__mutmut_10(receipts: Iterable[Receipt]) -> Dict[str, int]:
    """Count usage of governance reference IDs."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_id = _safe_str(item.get("id"))
            if ref_id:
                counter[ref_id] = 1

    return _sorted_counter(counter)


def x_governance_reference_usage__mutmut_11(receipts: Iterable[Receipt]) -> Dict[str, int]:
    """Count usage of governance reference IDs."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_id = _safe_str(item.get("id"))
            if ref_id:
                counter[ref_id] -= 1

    return _sorted_counter(counter)


def x_governance_reference_usage__mutmut_12(receipts: Iterable[Receipt]) -> Dict[str, int]:
    """Count usage of governance reference IDs."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_id = _safe_str(item.get("id"))
            if ref_id:
                counter[ref_id] += 2

    return _sorted_counter(counter)


def x_governance_reference_usage__mutmut_13(receipts: Iterable[Receipt]) -> Dict[str, int]:
    """Count usage of governance reference IDs."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_id = _safe_str(item.get("id"))
            if ref_id:
                counter[ref_id] += 1

    return _sorted_counter(None)

x_governance_reference_usage__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_governance_reference_usage__mutmut_1': x_governance_reference_usage__mutmut_1, 
    'x_governance_reference_usage__mutmut_2': x_governance_reference_usage__mutmut_2, 
    'x_governance_reference_usage__mutmut_3': x_governance_reference_usage__mutmut_3, 
    'x_governance_reference_usage__mutmut_4': x_governance_reference_usage__mutmut_4, 
    'x_governance_reference_usage__mutmut_5': x_governance_reference_usage__mutmut_5, 
    'x_governance_reference_usage__mutmut_6': x_governance_reference_usage__mutmut_6, 
    'x_governance_reference_usage__mutmut_7': x_governance_reference_usage__mutmut_7, 
    'x_governance_reference_usage__mutmut_8': x_governance_reference_usage__mutmut_8, 
    'x_governance_reference_usage__mutmut_9': x_governance_reference_usage__mutmut_9, 
    'x_governance_reference_usage__mutmut_10': x_governance_reference_usage__mutmut_10, 
    'x_governance_reference_usage__mutmut_11': x_governance_reference_usage__mutmut_11, 
    'x_governance_reference_usage__mutmut_12': x_governance_reference_usage__mutmut_12, 
    'x_governance_reference_usage__mutmut_13': x_governance_reference_usage__mutmut_13
}
x_governance_reference_usage__mutmut_orig.__name__ = 'x_governance_reference_usage'


def governance_reference_type_usage(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_governance_reference_type_usage__mutmut_orig, x_governance_reference_type_usage__mutmut_mutants, args, kwargs, None)


def x_governance_reference_type_usage__mutmut_orig(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count usage of governance reference types."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_type = _safe_str(item.get("type"))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_governance_reference_type_usage__mutmut_1(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count usage of governance reference types."""

    counter: Counter[str] = None

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_type = _safe_str(item.get("type"))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_governance_reference_type_usage__mutmut_2(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count usage of governance reference types."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_type = _safe_str(item.get("type"))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_governance_reference_type_usage__mutmut_3(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count usage of governance reference types."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            break

        for item in safe_traceability(r):
            ref_type = _safe_str(item.get("type"))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_governance_reference_type_usage__mutmut_4(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count usage of governance reference types."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(None):
            ref_type = _safe_str(item.get("type"))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_governance_reference_type_usage__mutmut_5(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count usage of governance reference types."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_type = None
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_governance_reference_type_usage__mutmut_6(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count usage of governance reference types."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_type = _safe_str(None)
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_governance_reference_type_usage__mutmut_7(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count usage of governance reference types."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_type = _safe_str(item.get(None))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_governance_reference_type_usage__mutmut_8(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count usage of governance reference types."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_type = _safe_str(item.get("XXtypeXX"))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_governance_reference_type_usage__mutmut_9(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count usage of governance reference types."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_type = _safe_str(item.get("TYPE"))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(counter)


def x_governance_reference_type_usage__mutmut_10(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count usage of governance reference types."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_type = _safe_str(item.get("type"))
            if ref_type:
                counter[ref_type] = 1

    return _sorted_counter(counter)


def x_governance_reference_type_usage__mutmut_11(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count usage of governance reference types."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_type = _safe_str(item.get("type"))
            if ref_type:
                counter[ref_type] -= 1

    return _sorted_counter(counter)


def x_governance_reference_type_usage__mutmut_12(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count usage of governance reference types."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_type = _safe_str(item.get("type"))
            if ref_type:
                counter[ref_type] += 2

    return _sorted_counter(counter)


def x_governance_reference_type_usage__mutmut_13(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count usage of governance reference types."""

    counter: Counter[str] = Counter()

    for r in receipts:
        if not isinstance(r, Mapping):
            continue

        for item in safe_traceability(r):
            ref_type = _safe_str(item.get("type"))
            if ref_type:
                counter[ref_type] += 1

    return _sorted_counter(None)

x_governance_reference_type_usage__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_governance_reference_type_usage__mutmut_1': x_governance_reference_type_usage__mutmut_1, 
    'x_governance_reference_type_usage__mutmut_2': x_governance_reference_type_usage__mutmut_2, 
    'x_governance_reference_type_usage__mutmut_3': x_governance_reference_type_usage__mutmut_3, 
    'x_governance_reference_type_usage__mutmut_4': x_governance_reference_type_usage__mutmut_4, 
    'x_governance_reference_type_usage__mutmut_5': x_governance_reference_type_usage__mutmut_5, 
    'x_governance_reference_type_usage__mutmut_6': x_governance_reference_type_usage__mutmut_6, 
    'x_governance_reference_type_usage__mutmut_7': x_governance_reference_type_usage__mutmut_7, 
    'x_governance_reference_type_usage__mutmut_8': x_governance_reference_type_usage__mutmut_8, 
    'x_governance_reference_type_usage__mutmut_9': x_governance_reference_type_usage__mutmut_9, 
    'x_governance_reference_type_usage__mutmut_10': x_governance_reference_type_usage__mutmut_10, 
    'x_governance_reference_type_usage__mutmut_11': x_governance_reference_type_usage__mutmut_11, 
    'x_governance_reference_type_usage__mutmut_12': x_governance_reference_type_usage__mutmut_12, 
    'x_governance_reference_type_usage__mutmut_13': x_governance_reference_type_usage__mutmut_13
}
x_governance_reference_type_usage__mutmut_orig.__name__ = 'x_governance_reference_type_usage'


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def build_metric_summary(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_metric_summary__mutmut_orig, x_build_metric_summary__mutmut_mutants, args, kwargs, None)


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_orig(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_1(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = None

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_2(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "XXdashboard_statusXX": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_3(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "DASHBOARD_STATUS": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_4(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "XXmetric_classificationXX": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_5(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "METRIC_CLASSIFICATION": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_6(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "XXread_onlyXX": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_7(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "READ_ONLY": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_8(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "XXdisplay_onlyXX": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_9(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "DISPLAY_ONLY": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_10(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "XXobservational_onlyXX": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_11(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "OBSERVATIONAL_ONLY": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_12(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "XXtotal_receiptsXX": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_13(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "TOTAL_RECEIPTS": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_14(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "XXunique_execution_idsXX": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_15(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "UNIQUE_EXECUTION_IDS": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_16(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(None),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_17(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "XXtotal_governance_referencesXX": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_18(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "TOTAL_GOVERNANCE_REFERENCES": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_19(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            None
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_20(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "XXunique_governance_referencesXX": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_21(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "UNIQUE_GOVERNANCE_REFERENCES": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_22(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            None
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_23(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "XXavg_refs_per_executionXX": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_24(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "AVG_REFS_PER_EXECUTION": average_references_per_execution(
            receipt_list
        ),
    }


# =============================================================================
# SUMMARY BUILDERS
# =============================================================================

def x_build_metric_summary__mutmut_25(
    receipts: Iterable[Receipt],
) -> Dict[str, MetricValue]:
    """
    Build canonical observational metrics.

    Metrics are NOT:
    - validation signals
    - proof signals
    - governance signals
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "dashboard_status": DASHBOARD_STATUS,
        "metric_classification": METRIC_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # counts
        "total_receipts": len(receipt_list),
        "unique_execution_ids": count_unique_execution_ids(receipt_list),

        # governance
        "total_governance_references": count_total_governance_references(
            receipt_list
        ),
        "unique_governance_references": count_unique_governance_references(
            receipt_list
        ),

        # derived
        "avg_refs_per_execution": average_references_per_execution(
            None
        ),
    }

x_build_metric_summary__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_metric_summary__mutmut_1': x_build_metric_summary__mutmut_1, 
    'x_build_metric_summary__mutmut_2': x_build_metric_summary__mutmut_2, 
    'x_build_metric_summary__mutmut_3': x_build_metric_summary__mutmut_3, 
    'x_build_metric_summary__mutmut_4': x_build_metric_summary__mutmut_4, 
    'x_build_metric_summary__mutmut_5': x_build_metric_summary__mutmut_5, 
    'x_build_metric_summary__mutmut_6': x_build_metric_summary__mutmut_6, 
    'x_build_metric_summary__mutmut_7': x_build_metric_summary__mutmut_7, 
    'x_build_metric_summary__mutmut_8': x_build_metric_summary__mutmut_8, 
    'x_build_metric_summary__mutmut_9': x_build_metric_summary__mutmut_9, 
    'x_build_metric_summary__mutmut_10': x_build_metric_summary__mutmut_10, 
    'x_build_metric_summary__mutmut_11': x_build_metric_summary__mutmut_11, 
    'x_build_metric_summary__mutmut_12': x_build_metric_summary__mutmut_12, 
    'x_build_metric_summary__mutmut_13': x_build_metric_summary__mutmut_13, 
    'x_build_metric_summary__mutmut_14': x_build_metric_summary__mutmut_14, 
    'x_build_metric_summary__mutmut_15': x_build_metric_summary__mutmut_15, 
    'x_build_metric_summary__mutmut_16': x_build_metric_summary__mutmut_16, 
    'x_build_metric_summary__mutmut_17': x_build_metric_summary__mutmut_17, 
    'x_build_metric_summary__mutmut_18': x_build_metric_summary__mutmut_18, 
    'x_build_metric_summary__mutmut_19': x_build_metric_summary__mutmut_19, 
    'x_build_metric_summary__mutmut_20': x_build_metric_summary__mutmut_20, 
    'x_build_metric_summary__mutmut_21': x_build_metric_summary__mutmut_21, 
    'x_build_metric_summary__mutmut_22': x_build_metric_summary__mutmut_22, 
    'x_build_metric_summary__mutmut_23': x_build_metric_summary__mutmut_23, 
    'x_build_metric_summary__mutmut_24': x_build_metric_summary__mutmut_24, 
    'x_build_metric_summary__mutmut_25': x_build_metric_summary__mutmut_25
}
x_build_metric_summary__mutmut_orig.__name__ = 'x_build_metric_summary'


def build_metric_payload(receipts: Iterable[Receipt]) -> Dict[str, object]:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_metric_payload__mutmut_orig, x_build_metric_payload__mutmut_mutants, args, kwargs, None)


def x_build_metric_payload__mutmut_orig(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_1(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = None

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_2(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "XXstatusXX": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_3(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "STATUS": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_4(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "XXREAD_ONLYXX",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_5(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "read_only",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_6(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "XXdashboard_statusXX": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_7(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "DASHBOARD_STATUS": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_8(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "XXread_onlyXX": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_9(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "READ_ONLY": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_10(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "XXdisplay_onlyXX": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_11(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "DISPLAY_ONLY": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_12(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "XXobservational_onlyXX": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_13(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "OBSERVATIONAL_ONLY": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_14(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "XXmetricsXX": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_15(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "METRICS": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_16(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(None),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_17(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "XXgovernance_reference_usageXX": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_18(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "GOVERNANCE_REFERENCE_USAGE": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_19(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            None
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_20(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "XXgovernance_reference_type_usageXX": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_21(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "GOVERNANCE_REFERENCE_TYPE_USAGE": governance_reference_type_usage(
            receipt_list
        ),
    }


def x_build_metric_payload__mutmut_22(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Build full dashboard payload.

    ✅ Safe for APIs
    ✅ Deterministic
    ✅ Non-authoritative
    """

    receipt_list = [r for r in receipts if isinstance(r, Mapping)]

    return {
        "status": "READ_ONLY",
        "dashboard_status": DASHBOARD_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # metrics
        "metrics": build_metric_summary(receipt_list),

        # distributions
        "governance_reference_usage": governance_reference_usage(
            receipt_list
        ),
        "governance_reference_type_usage": governance_reference_type_usage(
            None
        ),
    }

x_build_metric_payload__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_metric_payload__mutmut_1': x_build_metric_payload__mutmut_1, 
    'x_build_metric_payload__mutmut_2': x_build_metric_payload__mutmut_2, 
    'x_build_metric_payload__mutmut_3': x_build_metric_payload__mutmut_3, 
    'x_build_metric_payload__mutmut_4': x_build_metric_payload__mutmut_4, 
    'x_build_metric_payload__mutmut_5': x_build_metric_payload__mutmut_5, 
    'x_build_metric_payload__mutmut_6': x_build_metric_payload__mutmut_6, 
    'x_build_metric_payload__mutmut_7': x_build_metric_payload__mutmut_7, 
    'x_build_metric_payload__mutmut_8': x_build_metric_payload__mutmut_8, 
    'x_build_metric_payload__mutmut_9': x_build_metric_payload__mutmut_9, 
    'x_build_metric_payload__mutmut_10': x_build_metric_payload__mutmut_10, 
    'x_build_metric_payload__mutmut_11': x_build_metric_payload__mutmut_11, 
    'x_build_metric_payload__mutmut_12': x_build_metric_payload__mutmut_12, 
    'x_build_metric_payload__mutmut_13': x_build_metric_payload__mutmut_13, 
    'x_build_metric_payload__mutmut_14': x_build_metric_payload__mutmut_14, 
    'x_build_metric_payload__mutmut_15': x_build_metric_payload__mutmut_15, 
    'x_build_metric_payload__mutmut_16': x_build_metric_payload__mutmut_16, 
    'x_build_metric_payload__mutmut_17': x_build_metric_payload__mutmut_17, 
    'x_build_metric_payload__mutmut_18': x_build_metric_payload__mutmut_18, 
    'x_build_metric_payload__mutmut_19': x_build_metric_payload__mutmut_19, 
    'x_build_metric_payload__mutmut_20': x_build_metric_payload__mutmut_20, 
    'x_build_metric_payload__mutmut_21': x_build_metric_payload__mutmut_21, 
    'x_build_metric_payload__mutmut_22': x_build_metric_payload__mutmut_22
}
x_build_metric_payload__mutmut_orig.__name__ = 'x_build_metric_payload'


# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    "safe_traceability",
    "safe_execution_id",
    "count_receipts",
    "count_unique_execution_ids",
    "count_total_governance_references",
    "count_unique_governance_references",
    "average_references_per_execution",
    "governance_reference_usage",
    "governance_reference_type_usage",
    "build_metric_summary",
    "build_metric_payload",
]