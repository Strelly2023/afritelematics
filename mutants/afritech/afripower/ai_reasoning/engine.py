"""
AFRIPower AI Reasoning Engine

Read-only, interpretive-only pattern extraction.

This module MUST NEVER:
- execute runtime behavior
- validate truth
- enforce governance
- mutate receipts
- mutate proof artifacts
- create authority
- determine admissibility

This module is:
✅ observational
✅ interpretive
✅ non-authoritative
✅ deterministic
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Dict, List, Tuple

from afritech.afripower.ai_reasoning.constants import (
    DISPLAY_ONLY,
    INSIGHT_CLASSIFICATION,
    INTERPRETIVE_ONLY,
    OBSERVATIONAL_ONLY,
    READ_ONLY,
    REASONING_STATUS,
)

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
# SAFE EXTRACTION HELPERS
# =============================================================================


def _safe_str(value: object) -> str:
    args = [value]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__safe_str__mutmut_orig, x__safe_str__mutmut_mutants, args, kwargs, None)


# =============================================================================
# SAFE EXTRACTION HELPERS
# =============================================================================


def x__safe_str__mutmut_orig(value: object) -> str:
    """Safely normalize string values."""

    if isinstance(value, str):
        value = value.strip()
        if value:
            return value
    return ""


# =============================================================================
# SAFE EXTRACTION HELPERS
# =============================================================================


def x__safe_str__mutmut_1(value: object) -> str:
    """Safely normalize string values."""

    if isinstance(value, str):
        value = None
        if value:
            return value
    return ""


# =============================================================================
# SAFE EXTRACTION HELPERS
# =============================================================================


def x__safe_str__mutmut_2(value: object) -> str:
    """Safely normalize string values."""

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


def safe_traceability(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    args = [receipt]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_safe_traceability__mutmut_orig, x_safe_traceability__mutmut_mutants, args, kwargs, None)


def x_safe_traceability__mutmut_orig(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ No mutation
    ✅ Defensive filtering
    ✅ Deterministic output
    """

    raw = receipt.get(_TRACEABILITY_KEY, [])

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return ()

    result: List[Mapping[str, Any]] = []

    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x_safe_traceability__mutmut_1(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ No mutation
    ✅ Defensive filtering
    ✅ Deterministic output
    """

    raw = None

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return ()

    result: List[Mapping[str, Any]] = []

    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x_safe_traceability__mutmut_2(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ No mutation
    ✅ Defensive filtering
    ✅ Deterministic output
    """

    raw = receipt.get(None, [])

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return ()

    result: List[Mapping[str, Any]] = []

    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x_safe_traceability__mutmut_3(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ No mutation
    ✅ Defensive filtering
    ✅ Deterministic output
    """

    raw = receipt.get(_TRACEABILITY_KEY, None)

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return ()

    result: List[Mapping[str, Any]] = []

    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x_safe_traceability__mutmut_4(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ No mutation
    ✅ Defensive filtering
    ✅ Deterministic output
    """

    raw = receipt.get([])

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return ()

    result: List[Mapping[str, Any]] = []

    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x_safe_traceability__mutmut_5(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ No mutation
    ✅ Defensive filtering
    ✅ Deterministic output
    """

    raw = receipt.get(_TRACEABILITY_KEY, )

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return ()

    result: List[Mapping[str, Any]] = []

    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x_safe_traceability__mutmut_6(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ No mutation
    ✅ Defensive filtering
    ✅ Deterministic output
    """

    raw = receipt.get(_TRACEABILITY_KEY, [])

    if not isinstance(raw, Sequence) and isinstance(raw, (str, bytes)):
        return ()

    result: List[Mapping[str, Any]] = []

    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x_safe_traceability__mutmut_7(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ No mutation
    ✅ Defensive filtering
    ✅ Deterministic output
    """

    raw = receipt.get(_TRACEABILITY_KEY, [])

    if isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return ()

    result: List[Mapping[str, Any]] = []

    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x_safe_traceability__mutmut_8(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ No mutation
    ✅ Defensive filtering
    ✅ Deterministic output
    """

    raw = receipt.get(_TRACEABILITY_KEY, [])

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return ()

    result: List[Mapping[str, Any]] = None

    for item in raw:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x_safe_traceability__mutmut_9(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ No mutation
    ✅ Defensive filtering
    ✅ Deterministic output
    """

    raw = receipt.get(_TRACEABILITY_KEY, [])

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return ()

    result: List[Mapping[str, Any]] = []

    for item in raw:
        if isinstance(item, Mapping):
            result.append(None)

    return tuple(result)


def x_safe_traceability__mutmut_10(receipt: Receipt) -> Tuple[Mapping[str, Any], ...]:
    """
    Extract valid governance traceability entries.

    ✅ No mutation
    ✅ Defensive filtering
    ✅ Deterministic output
    """

    raw = receipt.get(_TRACEABILITY_KEY, [])

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return ()

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
    'x_safe_traceability__mutmut_9': x_safe_traceability__mutmut_9, 
    'x_safe_traceability__mutmut_10': x_safe_traceability__mutmut_10
}
x_safe_traceability__mutmut_orig.__name__ = 'x_safe_traceability'


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================


def extract_governance_reference_ids(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_extract_governance_reference_ids__mutmut_orig, x_extract_governance_reference_ids__mutmut_mutants, args, kwargs, None)


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================


def x_extract_governance_reference_ids__mutmut_orig(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference IDs (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_id = _safe_str(ref.get("id"))
            if ref_id:
                results.append(ref_id)

    return tuple(results)


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================


def x_extract_governance_reference_ids__mutmut_1(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference IDs (observational only)."""

    results: List[str] = None

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_id = _safe_str(ref.get("id"))
            if ref_id:
                results.append(ref_id)

    return tuple(results)


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================


def x_extract_governance_reference_ids__mutmut_2(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference IDs (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_id = _safe_str(ref.get("id"))
            if ref_id:
                results.append(ref_id)

    return tuple(results)


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================


def x_extract_governance_reference_ids__mutmut_3(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference IDs (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            break

        for ref in safe_traceability(receipt):
            ref_id = _safe_str(ref.get("id"))
            if ref_id:
                results.append(ref_id)

    return tuple(results)


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================


def x_extract_governance_reference_ids__mutmut_4(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference IDs (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(None):
            ref_id = _safe_str(ref.get("id"))
            if ref_id:
                results.append(ref_id)

    return tuple(results)


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================


def x_extract_governance_reference_ids__mutmut_5(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference IDs (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_id = None
            if ref_id:
                results.append(ref_id)

    return tuple(results)


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================


def x_extract_governance_reference_ids__mutmut_6(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference IDs (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_id = _safe_str(None)
            if ref_id:
                results.append(ref_id)

    return tuple(results)


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================


def x_extract_governance_reference_ids__mutmut_7(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference IDs (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_id = _safe_str(ref.get(None))
            if ref_id:
                results.append(ref_id)

    return tuple(results)


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================


def x_extract_governance_reference_ids__mutmut_8(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference IDs (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_id = _safe_str(ref.get("XXidXX"))
            if ref_id:
                results.append(ref_id)

    return tuple(results)


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================


def x_extract_governance_reference_ids__mutmut_9(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference IDs (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_id = _safe_str(ref.get("ID"))
            if ref_id:
                results.append(ref_id)

    return tuple(results)


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================


def x_extract_governance_reference_ids__mutmut_10(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference IDs (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_id = _safe_str(ref.get("id"))
            if ref_id:
                results.append(None)

    return tuple(results)


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================


def x_extract_governance_reference_ids__mutmut_11(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference IDs (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_id = _safe_str(ref.get("id"))
            if ref_id:
                results.append(ref_id)

    return tuple(None)

x_extract_governance_reference_ids__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_extract_governance_reference_ids__mutmut_1': x_extract_governance_reference_ids__mutmut_1, 
    'x_extract_governance_reference_ids__mutmut_2': x_extract_governance_reference_ids__mutmut_2, 
    'x_extract_governance_reference_ids__mutmut_3': x_extract_governance_reference_ids__mutmut_3, 
    'x_extract_governance_reference_ids__mutmut_4': x_extract_governance_reference_ids__mutmut_4, 
    'x_extract_governance_reference_ids__mutmut_5': x_extract_governance_reference_ids__mutmut_5, 
    'x_extract_governance_reference_ids__mutmut_6': x_extract_governance_reference_ids__mutmut_6, 
    'x_extract_governance_reference_ids__mutmut_7': x_extract_governance_reference_ids__mutmut_7, 
    'x_extract_governance_reference_ids__mutmut_8': x_extract_governance_reference_ids__mutmut_8, 
    'x_extract_governance_reference_ids__mutmut_9': x_extract_governance_reference_ids__mutmut_9, 
    'x_extract_governance_reference_ids__mutmut_10': x_extract_governance_reference_ids__mutmut_10, 
    'x_extract_governance_reference_ids__mutmut_11': x_extract_governance_reference_ids__mutmut_11
}
x_extract_governance_reference_ids__mutmut_orig.__name__ = 'x_extract_governance_reference_ids'


def extract_governance_reference_types(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_extract_governance_reference_types__mutmut_orig, x_extract_governance_reference_types__mutmut_mutants, args, kwargs, None)


def x_extract_governance_reference_types__mutmut_orig(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference types (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_type = _safe_str(ref.get("type"))
            if ref_type:
                results.append(ref_type)

    return tuple(results)


def x_extract_governance_reference_types__mutmut_1(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference types (observational only)."""

    results: List[str] = None

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_type = _safe_str(ref.get("type"))
            if ref_type:
                results.append(ref_type)

    return tuple(results)


def x_extract_governance_reference_types__mutmut_2(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference types (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_type = _safe_str(ref.get("type"))
            if ref_type:
                results.append(ref_type)

    return tuple(results)


def x_extract_governance_reference_types__mutmut_3(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference types (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            break

        for ref in safe_traceability(receipt):
            ref_type = _safe_str(ref.get("type"))
            if ref_type:
                results.append(ref_type)

    return tuple(results)


def x_extract_governance_reference_types__mutmut_4(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference types (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(None):
            ref_type = _safe_str(ref.get("type"))
            if ref_type:
                results.append(ref_type)

    return tuple(results)


def x_extract_governance_reference_types__mutmut_5(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference types (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_type = None
            if ref_type:
                results.append(ref_type)

    return tuple(results)


def x_extract_governance_reference_types__mutmut_6(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference types (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_type = _safe_str(None)
            if ref_type:
                results.append(ref_type)

    return tuple(results)


def x_extract_governance_reference_types__mutmut_7(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference types (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_type = _safe_str(ref.get(None))
            if ref_type:
                results.append(ref_type)

    return tuple(results)


def x_extract_governance_reference_types__mutmut_8(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference types (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_type = _safe_str(ref.get("XXtypeXX"))
            if ref_type:
                results.append(ref_type)

    return tuple(results)


def x_extract_governance_reference_types__mutmut_9(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference types (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_type = _safe_str(ref.get("TYPE"))
            if ref_type:
                results.append(ref_type)

    return tuple(results)


def x_extract_governance_reference_types__mutmut_10(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference types (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_type = _safe_str(ref.get("type"))
            if ref_type:
                results.append(None)

    return tuple(results)


def x_extract_governance_reference_types__mutmut_11(
    receipts: Iterable[Receipt],
) -> Tuple[str, ...]:
    """Extract governance reference types (observational only)."""

    results: List[str] = []

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            continue

        for ref in safe_traceability(receipt):
            ref_type = _safe_str(ref.get("type"))
            if ref_type:
                results.append(ref_type)

    return tuple(None)

x_extract_governance_reference_types__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_extract_governance_reference_types__mutmut_1': x_extract_governance_reference_types__mutmut_1, 
    'x_extract_governance_reference_types__mutmut_2': x_extract_governance_reference_types__mutmut_2, 
    'x_extract_governance_reference_types__mutmut_3': x_extract_governance_reference_types__mutmut_3, 
    'x_extract_governance_reference_types__mutmut_4': x_extract_governance_reference_types__mutmut_4, 
    'x_extract_governance_reference_types__mutmut_5': x_extract_governance_reference_types__mutmut_5, 
    'x_extract_governance_reference_types__mutmut_6': x_extract_governance_reference_types__mutmut_6, 
    'x_extract_governance_reference_types__mutmut_7': x_extract_governance_reference_types__mutmut_7, 
    'x_extract_governance_reference_types__mutmut_8': x_extract_governance_reference_types__mutmut_8, 
    'x_extract_governance_reference_types__mutmut_9': x_extract_governance_reference_types__mutmut_9, 
    'x_extract_governance_reference_types__mutmut_10': x_extract_governance_reference_types__mutmut_10, 
    'x_extract_governance_reference_types__mutmut_11': x_extract_governance_reference_types__mutmut_11
}
x_extract_governance_reference_types__mutmut_orig.__name__ = 'x_extract_governance_reference_types'


# =============================================================================
# FREQUENCY ANALYSIS
# =============================================================================


def _sorted_counter(counter: Counter) -> Dict[str, int]:
    args = [counter]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__sorted_counter__mutmut_orig, x__sorted_counter__mutmut_mutants, args, kwargs, None)


# =============================================================================
# FREQUENCY ANALYSIS
# =============================================================================


def x__sorted_counter__mutmut_orig(counter: Counter) -> Dict[str, int]:
    """
    Deterministic sorting:
        - by descending count
        - then lexicographically
    """

    return dict(
        sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


# =============================================================================
# FREQUENCY ANALYSIS
# =============================================================================


def x__sorted_counter__mutmut_1(counter: Counter) -> Dict[str, int]:
    """
    Deterministic sorting:
        - by descending count
        - then lexicographically
    """

    return dict(
        None
    )


# =============================================================================
# FREQUENCY ANALYSIS
# =============================================================================


def x__sorted_counter__mutmut_2(counter: Counter) -> Dict[str, int]:
    """
    Deterministic sorting:
        - by descending count
        - then lexicographically
    """

    return dict(
        sorted(
            None,
            key=lambda item: (-item[1], item[0]),
        )
    )


# =============================================================================
# FREQUENCY ANALYSIS
# =============================================================================


def x__sorted_counter__mutmut_3(counter: Counter) -> Dict[str, int]:
    """
    Deterministic sorting:
        - by descending count
        - then lexicographically
    """

    return dict(
        sorted(
            counter.items(),
            key=None,
        )
    )


# =============================================================================
# FREQUENCY ANALYSIS
# =============================================================================


def x__sorted_counter__mutmut_4(counter: Counter) -> Dict[str, int]:
    """
    Deterministic sorting:
        - by descending count
        - then lexicographically
    """

    return dict(
        sorted(
            key=lambda item: (-item[1], item[0]),
        )
    )


# =============================================================================
# FREQUENCY ANALYSIS
# =============================================================================


def x__sorted_counter__mutmut_5(counter: Counter) -> Dict[str, int]:
    """
    Deterministic sorting:
        - by descending count
        - then lexicographically
    """

    return dict(
        sorted(
            counter.items(),
            )
    )


# =============================================================================
# FREQUENCY ANALYSIS
# =============================================================================


def x__sorted_counter__mutmut_6(counter: Counter) -> Dict[str, int]:
    """
    Deterministic sorting:
        - by descending count
        - then lexicographically
    """

    return dict(
        sorted(
            counter.items(),
            key=lambda item: None,
        )
    )


# =============================================================================
# FREQUENCY ANALYSIS
# =============================================================================


def x__sorted_counter__mutmut_7(counter: Counter) -> Dict[str, int]:
    """
    Deterministic sorting:
        - by descending count
        - then lexicographically
    """

    return dict(
        sorted(
            counter.items(),
            key=lambda item: (+item[1], item[0]),
        )
    )


# =============================================================================
# FREQUENCY ANALYSIS
# =============================================================================


def x__sorted_counter__mutmut_8(counter: Counter) -> Dict[str, int]:
    """
    Deterministic sorting:
        - by descending count
        - then lexicographically
    """

    return dict(
        sorted(
            counter.items(),
            key=lambda item: (-item[2], item[0]),
        )
    )


# =============================================================================
# FREQUENCY ANALYSIS
# =============================================================================


def x__sorted_counter__mutmut_9(counter: Counter) -> Dict[str, int]:
    """
    Deterministic sorting:
        - by descending count
        - then lexicographically
    """

    return dict(
        sorted(
            counter.items(),
            key=lambda item: (-item[1], item[1]),
        )
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


def count_reference_frequency(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_count_reference_frequency__mutmut_orig, x_count_reference_frequency__mutmut_mutants, args, kwargs, None)


def x_count_reference_frequency__mutmut_orig(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count governance reference frequency."""

    counter = Counter(extract_governance_reference_ids(receipts))
    return _sorted_counter(counter)


def x_count_reference_frequency__mutmut_1(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count governance reference frequency."""

    counter = None
    return _sorted_counter(counter)


def x_count_reference_frequency__mutmut_2(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count governance reference frequency."""

    counter = Counter(None)
    return _sorted_counter(counter)


def x_count_reference_frequency__mutmut_3(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count governance reference frequency."""

    counter = Counter(extract_governance_reference_ids(None))
    return _sorted_counter(counter)


def x_count_reference_frequency__mutmut_4(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count governance reference frequency."""

    counter = Counter(extract_governance_reference_ids(receipts))
    return _sorted_counter(None)

x_count_reference_frequency__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_count_reference_frequency__mutmut_1': x_count_reference_frequency__mutmut_1, 
    'x_count_reference_frequency__mutmut_2': x_count_reference_frequency__mutmut_2, 
    'x_count_reference_frequency__mutmut_3': x_count_reference_frequency__mutmut_3, 
    'x_count_reference_frequency__mutmut_4': x_count_reference_frequency__mutmut_4
}
x_count_reference_frequency__mutmut_orig.__name__ = 'x_count_reference_frequency'


def count_reference_type_frequency(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_count_reference_type_frequency__mutmut_orig, x_count_reference_type_frequency__mutmut_mutants, args, kwargs, None)


def x_count_reference_type_frequency__mutmut_orig(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count governance reference type frequency."""

    counter = Counter(extract_governance_reference_types(receipts))
    return _sorted_counter(counter)


def x_count_reference_type_frequency__mutmut_1(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count governance reference type frequency."""

    counter = None
    return _sorted_counter(counter)


def x_count_reference_type_frequency__mutmut_2(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count governance reference type frequency."""

    counter = Counter(None)
    return _sorted_counter(counter)


def x_count_reference_type_frequency__mutmut_3(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count governance reference type frequency."""

    counter = Counter(extract_governance_reference_types(None))
    return _sorted_counter(counter)


def x_count_reference_type_frequency__mutmut_4(
    receipts: Iterable[Receipt],
) -> Dict[str, int]:
    """Count governance reference type frequency."""

    counter = Counter(extract_governance_reference_types(receipts))
    return _sorted_counter(None)

x_count_reference_type_frequency__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_count_reference_type_frequency__mutmut_1': x_count_reference_type_frequency__mutmut_1, 
    'x_count_reference_type_frequency__mutmut_2': x_count_reference_type_frequency__mutmut_2, 
    'x_count_reference_type_frequency__mutmut_3': x_count_reference_type_frequency__mutmut_3, 
    'x_count_reference_type_frequency__mutmut_4': x_count_reference_type_frequency__mutmut_4
}
x_count_reference_type_frequency__mutmut_orig.__name__ = 'x_count_reference_type_frequency'


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def extract_patterns(receipts: Iterable[Receipt]) -> Dict[str, object]:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_extract_patterns__mutmut_orig, x_extract_patterns__mutmut_mutants, args, kwargs, None)


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_orig(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_1(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = None

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_2(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = None
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_3(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(None)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_4(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = None

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_5(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(None)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_6(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = None
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_7(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(None)
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_8(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = None

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_9(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(None)

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_10(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "XXreasoning_statusXX": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_11(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "REASONING_STATUS": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_12(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "XXinsight_classificationXX": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_13(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "INSIGHT_CLASSIFICATION": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_14(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "XXread_onlyXX": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_15(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "READ_ONLY": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_16(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "XXdisplay_onlyXX": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_17(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "DISPLAY_ONLY": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_18(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "XXobservational_onlyXX": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_19(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "OBSERVATIONAL_ONLY": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_20(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "XXinterpretive_onlyXX": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_21(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "INTERPRETIVE_ONLY": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_22(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "XXtotal_receipts_observedXX": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_23(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "TOTAL_RECEIPTS_OBSERVED": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_24(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "XXunique_governance_idsXX": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_25(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "UNIQUE_GOVERNANCE_IDS": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_26(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "XXunique_governance_typesXX": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_27(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "UNIQUE_GOVERNANCE_TYPES": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_28(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "XXreference_frequencyXX": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_29(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "REFERENCE_FREQUENCY": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_30(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "XXreference_type_frequencyXX": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_31(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "REFERENCE_TYPE_FREQUENCY": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_32(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "XXmost_referenced_governance_idsXX": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_33(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "MOST_REFERENCED_GOVERNANCE_IDS": most_ids,
        "most_referenced_governance_types": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_34(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "XXmost_referenced_governance_typesXX": most_types,
    }


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================


def x_extract_patterns__mutmut_35(receipts: Iterable[Receipt]) -> Dict[str, object]:
    """
    Extract read-only reasoning patterns.

    ✅ Observational
    ✅ Non-authoritative
    ✅ Deterministic
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    reference_frequency = count_reference_frequency(receipt_list)
    reference_type_frequency = count_reference_type_frequency(receipt_list)

    most_ids: Tuple[str, ...] = tuple(reference_frequency.keys())
    most_types: Tuple[str, ...] = tuple(reference_type_frequency.keys())

    return {
        # status
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # observational metrics
        "total_receipts_observed": len(receipt_list),
        "unique_governance_ids": len(reference_frequency),
        "unique_governance_types": len(reference_type_frequency),

        # frequency analysis
        "reference_frequency": reference_frequency,
        "reference_type_frequency": reference_type_frequency,

        # ranking
        "most_referenced_governance_ids": most_ids,
        "MOST_REFERENCED_GOVERNANCE_TYPES": most_types,
    }

x_extract_patterns__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_extract_patterns__mutmut_1': x_extract_patterns__mutmut_1, 
    'x_extract_patterns__mutmut_2': x_extract_patterns__mutmut_2, 
    'x_extract_patterns__mutmut_3': x_extract_patterns__mutmut_3, 
    'x_extract_patterns__mutmut_4': x_extract_patterns__mutmut_4, 
    'x_extract_patterns__mutmut_5': x_extract_patterns__mutmut_5, 
    'x_extract_patterns__mutmut_6': x_extract_patterns__mutmut_6, 
    'x_extract_patterns__mutmut_7': x_extract_patterns__mutmut_7, 
    'x_extract_patterns__mutmut_8': x_extract_patterns__mutmut_8, 
    'x_extract_patterns__mutmut_9': x_extract_patterns__mutmut_9, 
    'x_extract_patterns__mutmut_10': x_extract_patterns__mutmut_10, 
    'x_extract_patterns__mutmut_11': x_extract_patterns__mutmut_11, 
    'x_extract_patterns__mutmut_12': x_extract_patterns__mutmut_12, 
    'x_extract_patterns__mutmut_13': x_extract_patterns__mutmut_13, 
    'x_extract_patterns__mutmut_14': x_extract_patterns__mutmut_14, 
    'x_extract_patterns__mutmut_15': x_extract_patterns__mutmut_15, 
    'x_extract_patterns__mutmut_16': x_extract_patterns__mutmut_16, 
    'x_extract_patterns__mutmut_17': x_extract_patterns__mutmut_17, 
    'x_extract_patterns__mutmut_18': x_extract_patterns__mutmut_18, 
    'x_extract_patterns__mutmut_19': x_extract_patterns__mutmut_19, 
    'x_extract_patterns__mutmut_20': x_extract_patterns__mutmut_20, 
    'x_extract_patterns__mutmut_21': x_extract_patterns__mutmut_21, 
    'x_extract_patterns__mutmut_22': x_extract_patterns__mutmut_22, 
    'x_extract_patterns__mutmut_23': x_extract_patterns__mutmut_23, 
    'x_extract_patterns__mutmut_24': x_extract_patterns__mutmut_24, 
    'x_extract_patterns__mutmut_25': x_extract_patterns__mutmut_25, 
    'x_extract_patterns__mutmut_26': x_extract_patterns__mutmut_26, 
    'x_extract_patterns__mutmut_27': x_extract_patterns__mutmut_27, 
    'x_extract_patterns__mutmut_28': x_extract_patterns__mutmut_28, 
    'x_extract_patterns__mutmut_29': x_extract_patterns__mutmut_29, 
    'x_extract_patterns__mutmut_30': x_extract_patterns__mutmut_30, 
    'x_extract_patterns__mutmut_31': x_extract_patterns__mutmut_31, 
    'x_extract_patterns__mutmut_32': x_extract_patterns__mutmut_32, 
    'x_extract_patterns__mutmut_33': x_extract_patterns__mutmut_33, 
    'x_extract_patterns__mutmut_34': x_extract_patterns__mutmut_34, 
    'x_extract_patterns__mutmut_35': x_extract_patterns__mutmut_35
}
x_extract_patterns__mutmut_orig.__name__ = 'x_extract_patterns'


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def generate_summary_insights(patterns: Mapping[str, object]) -> Dict[str, object]:
    args = [patterns]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_generate_summary_insights__mutmut_orig, x_generate_summary_insights__mutmut_mutants, args, kwargs, None)


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_orig(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_1(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = None
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_2(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get(None, 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_3(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", None)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_4(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get(0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_5(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", )
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_6(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("XXtotal_receipts_observedXX", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_7(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("TOTAL_RECEIPTS_OBSERVED", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_8(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 1)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_9(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = None

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_10(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get(None, 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_11(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", None)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_12(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get(0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_13(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", )

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_14(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("XXunique_governance_idsXX", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_15(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("UNIQUE_GOVERNANCE_IDS", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_16(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 1)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_17(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = None

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_18(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids * total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_19(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 1.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_20(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "XXinsight_typeXX": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_21(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "INSIGHT_TYPE": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_22(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "XXsummaryXX",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_23(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "SUMMARY",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_24(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "XXclassificationXX": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_25(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "CLASSIFICATION": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_26(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "XXnon_authoritativeXX": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_27(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "NON_AUTHORITATIVE": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_28(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": False,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_29(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "XXstatementsXX": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_30(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "STATEMENTS": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_31(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(None, 4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_32(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, None)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_33(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(4)}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_34(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, )}",
        ],
    }


# =============================================================================
# AGGREGATED INSIGHTS (SAFE)
# =============================================================================


def x_generate_summary_insights__mutmut_35(patterns: Mapping[str, object]) -> Dict[str, object]:
    """
    Generate high-level interpretive insights.

    ✅ Non-authoritative
    ✅ Hypothesis only
    """

    total = patterns.get("total_receipts_observed", 0)
    unique_ids = patterns.get("unique_governance_ids", 0)

    density = (unique_ids / total) if total else 0.0

    return {
        "insight_type": "summary",
        "classification": INSIGHT_CLASSIFICATION,
        "non_authoritative": True,
        "statements": [
            f"{total} receipts observed",
            f"{unique_ids} distinct governance references",
            f"governance density ≈ {round(density, 5)}",
        ],
    }

x_generate_summary_insights__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_generate_summary_insights__mutmut_1': x_generate_summary_insights__mutmut_1, 
    'x_generate_summary_insights__mutmut_2': x_generate_summary_insights__mutmut_2, 
    'x_generate_summary_insights__mutmut_3': x_generate_summary_insights__mutmut_3, 
    'x_generate_summary_insights__mutmut_4': x_generate_summary_insights__mutmut_4, 
    'x_generate_summary_insights__mutmut_5': x_generate_summary_insights__mutmut_5, 
    'x_generate_summary_insights__mutmut_6': x_generate_summary_insights__mutmut_6, 
    'x_generate_summary_insights__mutmut_7': x_generate_summary_insights__mutmut_7, 
    'x_generate_summary_insights__mutmut_8': x_generate_summary_insights__mutmut_8, 
    'x_generate_summary_insights__mutmut_9': x_generate_summary_insights__mutmut_9, 
    'x_generate_summary_insights__mutmut_10': x_generate_summary_insights__mutmut_10, 
    'x_generate_summary_insights__mutmut_11': x_generate_summary_insights__mutmut_11, 
    'x_generate_summary_insights__mutmut_12': x_generate_summary_insights__mutmut_12, 
    'x_generate_summary_insights__mutmut_13': x_generate_summary_insights__mutmut_13, 
    'x_generate_summary_insights__mutmut_14': x_generate_summary_insights__mutmut_14, 
    'x_generate_summary_insights__mutmut_15': x_generate_summary_insights__mutmut_15, 
    'x_generate_summary_insights__mutmut_16': x_generate_summary_insights__mutmut_16, 
    'x_generate_summary_insights__mutmut_17': x_generate_summary_insights__mutmut_17, 
    'x_generate_summary_insights__mutmut_18': x_generate_summary_insights__mutmut_18, 
    'x_generate_summary_insights__mutmut_19': x_generate_summary_insights__mutmut_19, 
    'x_generate_summary_insights__mutmut_20': x_generate_summary_insights__mutmut_20, 
    'x_generate_summary_insights__mutmut_21': x_generate_summary_insights__mutmut_21, 
    'x_generate_summary_insights__mutmut_22': x_generate_summary_insights__mutmut_22, 
    'x_generate_summary_insights__mutmut_23': x_generate_summary_insights__mutmut_23, 
    'x_generate_summary_insights__mutmut_24': x_generate_summary_insights__mutmut_24, 
    'x_generate_summary_insights__mutmut_25': x_generate_summary_insights__mutmut_25, 
    'x_generate_summary_insights__mutmut_26': x_generate_summary_insights__mutmut_26, 
    'x_generate_summary_insights__mutmut_27': x_generate_summary_insights__mutmut_27, 
    'x_generate_summary_insights__mutmut_28': x_generate_summary_insights__mutmut_28, 
    'x_generate_summary_insights__mutmut_29': x_generate_summary_insights__mutmut_29, 
    'x_generate_summary_insights__mutmut_30': x_generate_summary_insights__mutmut_30, 
    'x_generate_summary_insights__mutmut_31': x_generate_summary_insights__mutmut_31, 
    'x_generate_summary_insights__mutmut_32': x_generate_summary_insights__mutmut_32, 
    'x_generate_summary_insights__mutmut_33': x_generate_summary_insights__mutmut_33, 
    'x_generate_summary_insights__mutmut_34': x_generate_summary_insights__mutmut_34, 
    'x_generate_summary_insights__mutmut_35': x_generate_summary_insights__mutmut_35
}
x_generate_summary_insights__mutmut_orig.__name__ = 'x_generate_summary_insights'


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def build_reasoning_payload(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_reasoning_payload__mutmut_orig, x_build_reasoning_payload__mutmut_mutants, args, kwargs, None)


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_orig(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_1(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = None
    summary = generate_summary_insights(patterns)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_2(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(None)
    summary = generate_summary_insights(patterns)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_3(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = None

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_4(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(None)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_5(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "XXstatusXX": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_6(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "STATUS": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_7(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "status": "XXREAD_ONLYXX",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_8(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "status": "read_only",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_9(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "status": "READ_ONLY",
        "XXreasoning_statusXX": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_10(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "status": "READ_ONLY",
        "REASONING_STATUS": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_11(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "XXread_onlyXX": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_12(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "READ_ONLY": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_13(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "XXdisplay_onlyXX": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_14(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "DISPLAY_ONLY": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_15(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "XXobservational_onlyXX": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_16(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "OBSERVATIONAL_ONLY": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_17(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "XXinterpretive_onlyXX": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_18(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "INTERPRETIVE_ONLY": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_19(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "XXpatternsXX": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_20(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "PATTERNS": patterns,
        "insights": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_21(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "XXinsightsXX": (summary,),
    }


# =============================================================================
# PUBLIC PAYLOAD BUILDER
# =============================================================================


def x_build_reasoning_payload__mutmut_22(
    receipts: Iterable[Receipt],
) -> Dict[str, object]:
    """
    Build canonical AFRIPower reasoning payload.

    ✅ Read-only
    ✅ Deterministic
    ✅ Safe for dashboards / APIs
    """

    patterns = extract_patterns(receipts)
    summary = generate_summary_insights(patterns)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # outputs
        "patterns": patterns,
        "INSIGHTS": (summary,),
    }

x_build_reasoning_payload__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_reasoning_payload__mutmut_1': x_build_reasoning_payload__mutmut_1, 
    'x_build_reasoning_payload__mutmut_2': x_build_reasoning_payload__mutmut_2, 
    'x_build_reasoning_payload__mutmut_3': x_build_reasoning_payload__mutmut_3, 
    'x_build_reasoning_payload__mutmut_4': x_build_reasoning_payload__mutmut_4, 
    'x_build_reasoning_payload__mutmut_5': x_build_reasoning_payload__mutmut_5, 
    'x_build_reasoning_payload__mutmut_6': x_build_reasoning_payload__mutmut_6, 
    'x_build_reasoning_payload__mutmut_7': x_build_reasoning_payload__mutmut_7, 
    'x_build_reasoning_payload__mutmut_8': x_build_reasoning_payload__mutmut_8, 
    'x_build_reasoning_payload__mutmut_9': x_build_reasoning_payload__mutmut_9, 
    'x_build_reasoning_payload__mutmut_10': x_build_reasoning_payload__mutmut_10, 
    'x_build_reasoning_payload__mutmut_11': x_build_reasoning_payload__mutmut_11, 
    'x_build_reasoning_payload__mutmut_12': x_build_reasoning_payload__mutmut_12, 
    'x_build_reasoning_payload__mutmut_13': x_build_reasoning_payload__mutmut_13, 
    'x_build_reasoning_payload__mutmut_14': x_build_reasoning_payload__mutmut_14, 
    'x_build_reasoning_payload__mutmut_15': x_build_reasoning_payload__mutmut_15, 
    'x_build_reasoning_payload__mutmut_16': x_build_reasoning_payload__mutmut_16, 
    'x_build_reasoning_payload__mutmut_17': x_build_reasoning_payload__mutmut_17, 
    'x_build_reasoning_payload__mutmut_18': x_build_reasoning_payload__mutmut_18, 
    'x_build_reasoning_payload__mutmut_19': x_build_reasoning_payload__mutmut_19, 
    'x_build_reasoning_payload__mutmut_20': x_build_reasoning_payload__mutmut_20, 
    'x_build_reasoning_payload__mutmut_21': x_build_reasoning_payload__mutmut_21, 
    'x_build_reasoning_payload__mutmut_22': x_build_reasoning_payload__mutmut_22
}
x_build_reasoning_payload__mutmut_orig.__name__ = 'x_build_reasoning_payload'


# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    "safe_traceability",
    "extract_governance_reference_ids",
    "extract_governance_reference_types",
    "count_reference_frequency",
    "count_reference_type_frequency",
    "extract_patterns",
    "generate_summary_insights",
    "build_reasoning_payload",
]
