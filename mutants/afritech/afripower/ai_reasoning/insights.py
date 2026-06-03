"""
AFRIPower AI Reasoning Insights

Read-only, interpretive-only insight generation.

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

from collections.abc import Mapping
from typing import Any, Dict, Tuple, List

from afritech.afripower.ai_reasoning.constants import (
    DISPLAY_ONLY,
    INSIGHT_CLASSIFICATION,
    INTERPRETIVE_ONLY,
    OBSERVATIONAL_ONLY,
    READ_ONLY,
    REASONING_STATUS,
    ALLOWED_INSIGHT_TYPES,
)

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_FREQUENCY_THRESHOLD = 5
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
# SAFE NORMALIZATION
# =============================================================================

def _safe_int(value: object) -> int:
    args = [value]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__safe_int__mutmut_orig, x__safe_int__mutmut_mutants, args, kwargs, None)


# =============================================================================
# SAFE NORMALIZATION
# =============================================================================

def x__safe_int__mutmut_orig(value: object) -> int:
    return value if isinstance(value, int) and value >= 0 else 0


# =============================================================================
# SAFE NORMALIZATION
# =============================================================================

def x__safe_int__mutmut_1(value: object) -> int:
    return value if isinstance(value, int) or value >= 0 else 0


# =============================================================================
# SAFE NORMALIZATION
# =============================================================================

def x__safe_int__mutmut_2(value: object) -> int:
    return value if isinstance(value, int) and value > 0 else 0


# =============================================================================
# SAFE NORMALIZATION
# =============================================================================

def x__safe_int__mutmut_3(value: object) -> int:
    return value if isinstance(value, int) and value >= 1 else 0


# =============================================================================
# SAFE NORMALIZATION
# =============================================================================

def x__safe_int__mutmut_4(value: object) -> int:
    return value if isinstance(value, int) and value >= 0 else 1

x__safe_int__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__safe_int__mutmut_1': x__safe_int__mutmut_1, 
    'x__safe_int__mutmut_2': x__safe_int__mutmut_2, 
    'x__safe_int__mutmut_3': x__safe_int__mutmut_3, 
    'x__safe_int__mutmut_4': x__safe_int__mutmut_4
}
x__safe_int__mutmut_orig.__name__ = 'x__safe_int'


def _safe_str(value: object) -> str:
    args = [value]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__safe_str__mutmut_orig, x__safe_str__mutmut_mutants, args, kwargs, None)


def x__safe_str__mutmut_orig(value: object) -> str:
    if isinstance(value, str):
        value = value.strip()
        if value:
            return value
    return ""


def x__safe_str__mutmut_1(value: object) -> str:
    if isinstance(value, str):
        value = None
        if value:
            return value
    return ""


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


def _safe_frequency_map(patterns: Mapping[str, Any]) -> Dict[str, int]:
    args = [patterns]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__safe_frequency_map__mutmut_orig, x__safe_frequency_map__mutmut_mutants, args, kwargs, None)


def x__safe_frequency_map__mutmut_orig(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_frequency_map__mutmut_1(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = None

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_frequency_map__mutmut_2(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get(None, {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_frequency_map__mutmut_3(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", None)

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_frequency_map__mutmut_4(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get({})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_frequency_map__mutmut_5(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", )

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_frequency_map__mutmut_6(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("XXreference_frequencyXX", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_frequency_map__mutmut_7(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("REFERENCE_FREQUENCY", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_frequency_map__mutmut_8(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", {})

    if isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_frequency_map__mutmut_9(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = None

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_frequency_map__mutmut_10(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = None
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_frequency_map__mutmut_11(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(None)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_frequency_map__mutmut_12(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = None

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_frequency_map__mutmut_13(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(None)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_frequency_map__mutmut_14(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = None

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_frequency_map__mutmut_15(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(None)


def x__safe_frequency_map__mutmut_16(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(None, key=lambda item: (-item[1], item[0])))


def x__safe_frequency_map__mutmut_17(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=None))


def x__safe_frequency_map__mutmut_18(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(key=lambda item: (-item[1], item[0])))


def x__safe_frequency_map__mutmut_19(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), ))


def x__safe_frequency_map__mutmut_20(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: None))


def x__safe_frequency_map__mutmut_21(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (+item[1], item[0])))


def x__safe_frequency_map__mutmut_22(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (-item[2], item[0])))


def x__safe_frequency_map__mutmut_23(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference frequency.

    ✅ Filters invalid entries
    ✅ Deterministic ordering
    """

    value = patterns.get("reference_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    # deterministic ordering
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[1])))

x__safe_frequency_map__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__safe_frequency_map__mutmut_1': x__safe_frequency_map__mutmut_1, 
    'x__safe_frequency_map__mutmut_2': x__safe_frequency_map__mutmut_2, 
    'x__safe_frequency_map__mutmut_3': x__safe_frequency_map__mutmut_3, 
    'x__safe_frequency_map__mutmut_4': x__safe_frequency_map__mutmut_4, 
    'x__safe_frequency_map__mutmut_5': x__safe_frequency_map__mutmut_5, 
    'x__safe_frequency_map__mutmut_6': x__safe_frequency_map__mutmut_6, 
    'x__safe_frequency_map__mutmut_7': x__safe_frequency_map__mutmut_7, 
    'x__safe_frequency_map__mutmut_8': x__safe_frequency_map__mutmut_8, 
    'x__safe_frequency_map__mutmut_9': x__safe_frequency_map__mutmut_9, 
    'x__safe_frequency_map__mutmut_10': x__safe_frequency_map__mutmut_10, 
    'x__safe_frequency_map__mutmut_11': x__safe_frequency_map__mutmut_11, 
    'x__safe_frequency_map__mutmut_12': x__safe_frequency_map__mutmut_12, 
    'x__safe_frequency_map__mutmut_13': x__safe_frequency_map__mutmut_13, 
    'x__safe_frequency_map__mutmut_14': x__safe_frequency_map__mutmut_14, 
    'x__safe_frequency_map__mutmut_15': x__safe_frequency_map__mutmut_15, 
    'x__safe_frequency_map__mutmut_16': x__safe_frequency_map__mutmut_16, 
    'x__safe_frequency_map__mutmut_17': x__safe_frequency_map__mutmut_17, 
    'x__safe_frequency_map__mutmut_18': x__safe_frequency_map__mutmut_18, 
    'x__safe_frequency_map__mutmut_19': x__safe_frequency_map__mutmut_19, 
    'x__safe_frequency_map__mutmut_20': x__safe_frequency_map__mutmut_20, 
    'x__safe_frequency_map__mutmut_21': x__safe_frequency_map__mutmut_21, 
    'x__safe_frequency_map__mutmut_22': x__safe_frequency_map__mutmut_22, 
    'x__safe_frequency_map__mutmut_23': x__safe_frequency_map__mutmut_23
}
x__safe_frequency_map__mutmut_orig.__name__ = 'x__safe_frequency_map'


def _safe_type_frequency_map(patterns: Mapping[str, Any]) -> Dict[str, int]:
    args = [patterns]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__safe_type_frequency_map__mutmut_orig, x__safe_type_frequency_map__mutmut_mutants, args, kwargs, None)


def x__safe_type_frequency_map__mutmut_orig(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_type_frequency_map__mutmut_1(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = None

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_type_frequency_map__mutmut_2(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get(None, {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_type_frequency_map__mutmut_3(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", None)

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_type_frequency_map__mutmut_4(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get({})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_type_frequency_map__mutmut_5(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", )

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_type_frequency_map__mutmut_6(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("XXreference_type_frequencyXX", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_type_frequency_map__mutmut_7(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("REFERENCE_TYPE_FREQUENCY", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_type_frequency_map__mutmut_8(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", {})

    if isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_type_frequency_map__mutmut_9(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = None

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_type_frequency_map__mutmut_10(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = None
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_type_frequency_map__mutmut_11(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(None)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_type_frequency_map__mutmut_12(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = None

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_type_frequency_map__mutmut_13(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(None)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_type_frequency_map__mutmut_14(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = None

    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def x__safe_type_frequency_map__mutmut_15(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(None)


def x__safe_type_frequency_map__mutmut_16(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(None, key=lambda item: (-item[1], item[0])))


def x__safe_type_frequency_map__mutmut_17(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=None))


def x__safe_type_frequency_map__mutmut_18(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(key=lambda item: (-item[1], item[0])))


def x__safe_type_frequency_map__mutmut_19(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), ))


def x__safe_type_frequency_map__mutmut_20(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: None))


def x__safe_type_frequency_map__mutmut_21(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: (+item[1], item[0])))


def x__safe_type_frequency_map__mutmut_22(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: (-item[2], item[0])))


def x__safe_type_frequency_map__mutmut_23(patterns: Mapping[str, Any]) -> Dict[str, int]:
    """
    Normalize governance reference type frequency.
    """

    value = patterns.get("reference_type_frequency", {})

    if not isinstance(value, Mapping):
        return {}

    result: Dict[str, int] = {}

    for key, count in value.items():
        key_str = _safe_str(key)
        count_int = _safe_int(count)

        if key_str:
            result[key_str] = count_int

    return dict(sorted(result.items(), key=lambda item: (-item[1], item[1])))

x__safe_type_frequency_map__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__safe_type_frequency_map__mutmut_1': x__safe_type_frequency_map__mutmut_1, 
    'x__safe_type_frequency_map__mutmut_2': x__safe_type_frequency_map__mutmut_2, 
    'x__safe_type_frequency_map__mutmut_3': x__safe_type_frequency_map__mutmut_3, 
    'x__safe_type_frequency_map__mutmut_4': x__safe_type_frequency_map__mutmut_4, 
    'x__safe_type_frequency_map__mutmut_5': x__safe_type_frequency_map__mutmut_5, 
    'x__safe_type_frequency_map__mutmut_6': x__safe_type_frequency_map__mutmut_6, 
    'x__safe_type_frequency_map__mutmut_7': x__safe_type_frequency_map__mutmut_7, 
    'x__safe_type_frequency_map__mutmut_8': x__safe_type_frequency_map__mutmut_8, 
    'x__safe_type_frequency_map__mutmut_9': x__safe_type_frequency_map__mutmut_9, 
    'x__safe_type_frequency_map__mutmut_10': x__safe_type_frequency_map__mutmut_10, 
    'x__safe_type_frequency_map__mutmut_11': x__safe_type_frequency_map__mutmut_11, 
    'x__safe_type_frequency_map__mutmut_12': x__safe_type_frequency_map__mutmut_12, 
    'x__safe_type_frequency_map__mutmut_13': x__safe_type_frequency_map__mutmut_13, 
    'x__safe_type_frequency_map__mutmut_14': x__safe_type_frequency_map__mutmut_14, 
    'x__safe_type_frequency_map__mutmut_15': x__safe_type_frequency_map__mutmut_15, 
    'x__safe_type_frequency_map__mutmut_16': x__safe_type_frequency_map__mutmut_16, 
    'x__safe_type_frequency_map__mutmut_17': x__safe_type_frequency_map__mutmut_17, 
    'x__safe_type_frequency_map__mutmut_18': x__safe_type_frequency_map__mutmut_18, 
    'x__safe_type_frequency_map__mutmut_19': x__safe_type_frequency_map__mutmut_19, 
    'x__safe_type_frequency_map__mutmut_20': x__safe_type_frequency_map__mutmut_20, 
    'x__safe_type_frequency_map__mutmut_21': x__safe_type_frequency_map__mutmut_21, 
    'x__safe_type_frequency_map__mutmut_22': x__safe_type_frequency_map__mutmut_22, 
    'x__safe_type_frequency_map__mutmut_23': x__safe_type_frequency_map__mutmut_23
}
x__safe_type_frequency_map__mutmut_orig.__name__ = 'x__safe_type_frequency_map'


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def _build_insight(payload: Dict[str, Any]) -> Dict[str, object]:
    args = [payload]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__build_insight__mutmut_orig, x__build_insight__mutmut_mutants, args, kwargs, None)


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_orig(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_1(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = None

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_2(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get(None, "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_3(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", None)

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_4(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_5(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", )

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_6(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("XXtypeXX", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_7(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("TYPE", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_8(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "XXhypothesisXX")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_9(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "HYPOTHESIS")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_10(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_11(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = None

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_12(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "XXhypothesisXX"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_13(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "HYPOTHESIS"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_14(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "XXtypeXX": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_15(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "TYPE": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_16(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "XXcategoryXX": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_17(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "CATEGORY": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_18(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(None),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_19(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get(None)),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_20(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("XXcategoryXX")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_21(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("CATEGORY")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_22(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "XXstatementXX": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_23(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "STATEMENT": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_24(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(None),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_25(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get(None)),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_26(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("XXstatementXX")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_27(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("STATEMENT")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_28(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "XXcountXX": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_29(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "COUNT": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_30(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(None),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_31(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get(None)),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_32(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("XXcountXX")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_33(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("COUNT")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_34(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "XXreference_idXX": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_35(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "REFERENCE_ID": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_36(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(None),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_37(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get(None)),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_38(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("XXreference_idXX")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_39(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("REFERENCE_ID")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_40(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "XXreference_typeXX": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_41(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "REFERENCE_TYPE": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_42(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(None),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_43(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get(None)),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_44(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("XXreference_typeXX")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_45(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("REFERENCE_TYPE")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_46(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "XXreasoning_statusXX": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_47(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "REASONING_STATUS": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_48(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "XXinsight_classificationXX": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_49(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "INSIGHT_CLASSIFICATION": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_50(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "XXread_onlyXX": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_51(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "READ_ONLY": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_52(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "XXdisplay_onlyXX": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_53(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "DISPLAY_ONLY": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_54(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "XXobservational_onlyXX": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_55(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "OBSERVATIONAL_ONLY": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_56(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "XXinterpretive_onlyXX": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_57(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "INTERPRETIVE_ONLY": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_58(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "XXauthoritativeXX": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_59(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "AUTHORITATIVE": False,
    }


# =============================================================================
# INSIGHT GENERATORS
# =============================================================================

def x__build_insight__mutmut_60(payload: Dict[str, Any]) -> Dict[str, object]:
    """
    Normalize and enforce safe insight structure.
    """

    insight_type = payload.get("type", "hypothesis")

    if insight_type not in ALLOWED_INSIGHT_TYPES:
        insight_type = "hypothesis"

    return {
        "type": insight_type,
        "category": _safe_str(payload.get("category")),
        "statement": _safe_str(payload.get("statement")),
        "count": _safe_int(payload.get("count")),

        # optional reference fields
        "reference_id": _safe_str(payload.get("reference_id")),
        "reference_type": _safe_str(payload.get("reference_type")),

        # reasoning metadata
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # safety flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        # authority guarantee
        "authoritative": True,
    }

x__build_insight__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__build_insight__mutmut_1': x__build_insight__mutmut_1, 
    'x__build_insight__mutmut_2': x__build_insight__mutmut_2, 
    'x__build_insight__mutmut_3': x__build_insight__mutmut_3, 
    'x__build_insight__mutmut_4': x__build_insight__mutmut_4, 
    'x__build_insight__mutmut_5': x__build_insight__mutmut_5, 
    'x__build_insight__mutmut_6': x__build_insight__mutmut_6, 
    'x__build_insight__mutmut_7': x__build_insight__mutmut_7, 
    'x__build_insight__mutmut_8': x__build_insight__mutmut_8, 
    'x__build_insight__mutmut_9': x__build_insight__mutmut_9, 
    'x__build_insight__mutmut_10': x__build_insight__mutmut_10, 
    'x__build_insight__mutmut_11': x__build_insight__mutmut_11, 
    'x__build_insight__mutmut_12': x__build_insight__mutmut_12, 
    'x__build_insight__mutmut_13': x__build_insight__mutmut_13, 
    'x__build_insight__mutmut_14': x__build_insight__mutmut_14, 
    'x__build_insight__mutmut_15': x__build_insight__mutmut_15, 
    'x__build_insight__mutmut_16': x__build_insight__mutmut_16, 
    'x__build_insight__mutmut_17': x__build_insight__mutmut_17, 
    'x__build_insight__mutmut_18': x__build_insight__mutmut_18, 
    'x__build_insight__mutmut_19': x__build_insight__mutmut_19, 
    'x__build_insight__mutmut_20': x__build_insight__mutmut_20, 
    'x__build_insight__mutmut_21': x__build_insight__mutmut_21, 
    'x__build_insight__mutmut_22': x__build_insight__mutmut_22, 
    'x__build_insight__mutmut_23': x__build_insight__mutmut_23, 
    'x__build_insight__mutmut_24': x__build_insight__mutmut_24, 
    'x__build_insight__mutmut_25': x__build_insight__mutmut_25, 
    'x__build_insight__mutmut_26': x__build_insight__mutmut_26, 
    'x__build_insight__mutmut_27': x__build_insight__mutmut_27, 
    'x__build_insight__mutmut_28': x__build_insight__mutmut_28, 
    'x__build_insight__mutmut_29': x__build_insight__mutmut_29, 
    'x__build_insight__mutmut_30': x__build_insight__mutmut_30, 
    'x__build_insight__mutmut_31': x__build_insight__mutmut_31, 
    'x__build_insight__mutmut_32': x__build_insight__mutmut_32, 
    'x__build_insight__mutmut_33': x__build_insight__mutmut_33, 
    'x__build_insight__mutmut_34': x__build_insight__mutmut_34, 
    'x__build_insight__mutmut_35': x__build_insight__mutmut_35, 
    'x__build_insight__mutmut_36': x__build_insight__mutmut_36, 
    'x__build_insight__mutmut_37': x__build_insight__mutmut_37, 
    'x__build_insight__mutmut_38': x__build_insight__mutmut_38, 
    'x__build_insight__mutmut_39': x__build_insight__mutmut_39, 
    'x__build_insight__mutmut_40': x__build_insight__mutmut_40, 
    'x__build_insight__mutmut_41': x__build_insight__mutmut_41, 
    'x__build_insight__mutmut_42': x__build_insight__mutmut_42, 
    'x__build_insight__mutmut_43': x__build_insight__mutmut_43, 
    'x__build_insight__mutmut_44': x__build_insight__mutmut_44, 
    'x__build_insight__mutmut_45': x__build_insight__mutmut_45, 
    'x__build_insight__mutmut_46': x__build_insight__mutmut_46, 
    'x__build_insight__mutmut_47': x__build_insight__mutmut_47, 
    'x__build_insight__mutmut_48': x__build_insight__mutmut_48, 
    'x__build_insight__mutmut_49': x__build_insight__mutmut_49, 
    'x__build_insight__mutmut_50': x__build_insight__mutmut_50, 
    'x__build_insight__mutmut_51': x__build_insight__mutmut_51, 
    'x__build_insight__mutmut_52': x__build_insight__mutmut_52, 
    'x__build_insight__mutmut_53': x__build_insight__mutmut_53, 
    'x__build_insight__mutmut_54': x__build_insight__mutmut_54, 
    'x__build_insight__mutmut_55': x__build_insight__mutmut_55, 
    'x__build_insight__mutmut_56': x__build_insight__mutmut_56, 
    'x__build_insight__mutmut_57': x__build_insight__mutmut_57, 
    'x__build_insight__mutmut_58': x__build_insight__mutmut_58, 
    'x__build_insight__mutmut_59': x__build_insight__mutmut_59, 
    'x__build_insight__mutmut_60': x__build_insight__mutmut_60
}
x__build_insight__mutmut_orig.__name__ = 'x__build_insight'


# -----------------------------------------------------------------------------

def generate_reference_frequency_insights(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    args = [patterns, threshold]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_generate_reference_frequency_insights__mutmut_orig, x_generate_reference_frequency_insights__mutmut_mutants, args, kwargs, None)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_orig(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_frequency",
                        "reference_id": ref_id,
                        "count": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_1(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = None

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_frequency",
                        "reference_id": ref_id,
                        "count": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_2(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = None

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_frequency",
                        "reference_id": ref_id,
                        "count": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_3(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(None)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_frequency",
                        "reference_id": ref_id,
                        "count": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_4(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count >= threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_frequency",
                        "reference_id": ref_id,
                        "count": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_5(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                None
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_6(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    None
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_7(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "XXtypeXX": "hypothesis",
                        "category": "reference_frequency",
                        "reference_id": ref_id,
                        "count": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_8(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "TYPE": "hypothesis",
                        "category": "reference_frequency",
                        "reference_id": ref_id,
                        "count": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_9(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "XXhypothesisXX",
                        "category": "reference_frequency",
                        "reference_id": ref_id,
                        "count": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_10(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "HYPOTHESIS",
                        "category": "reference_frequency",
                        "reference_id": ref_id,
                        "count": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_11(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "XXcategoryXX": "reference_frequency",
                        "reference_id": ref_id,
                        "count": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_12(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "CATEGORY": "reference_frequency",
                        "reference_id": ref_id,
                        "count": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_13(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "XXreference_frequencyXX",
                        "reference_id": ref_id,
                        "count": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_14(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "REFERENCE_FREQUENCY",
                        "reference_id": ref_id,
                        "count": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_15(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_frequency",
                        "XXreference_idXX": ref_id,
                        "count": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_16(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_frequency",
                        "REFERENCE_ID": ref_id,
                        "count": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_17(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_frequency",
                        "reference_id": ref_id,
                        "XXcountXX": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_18(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_frequency",
                        "reference_id": ref_id,
                        "COUNT": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_19(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_frequency",
                        "reference_id": ref_id,
                        "count": count,
                        "XXstatementXX": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_20(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_frequency",
                        "reference_id": ref_id,
                        "count": count,
                        "STATEMENT": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_frequency_insights__mutmut_21(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance reference frequency.

    ✅ Hypotheses only
    ✅ Non-authoritative
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_frequency_map(patterns)

    for ref_id, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_frequency",
                        "reference_id": ref_id,
                        "count": count,
                        "statement": (
                            f"{ref_id} appears frequently across observed "
                            f"executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(None)

x_generate_reference_frequency_insights__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_generate_reference_frequency_insights__mutmut_1': x_generate_reference_frequency_insights__mutmut_1, 
    'x_generate_reference_frequency_insights__mutmut_2': x_generate_reference_frequency_insights__mutmut_2, 
    'x_generate_reference_frequency_insights__mutmut_3': x_generate_reference_frequency_insights__mutmut_3, 
    'x_generate_reference_frequency_insights__mutmut_4': x_generate_reference_frequency_insights__mutmut_4, 
    'x_generate_reference_frequency_insights__mutmut_5': x_generate_reference_frequency_insights__mutmut_5, 
    'x_generate_reference_frequency_insights__mutmut_6': x_generate_reference_frequency_insights__mutmut_6, 
    'x_generate_reference_frequency_insights__mutmut_7': x_generate_reference_frequency_insights__mutmut_7, 
    'x_generate_reference_frequency_insights__mutmut_8': x_generate_reference_frequency_insights__mutmut_8, 
    'x_generate_reference_frequency_insights__mutmut_9': x_generate_reference_frequency_insights__mutmut_9, 
    'x_generate_reference_frequency_insights__mutmut_10': x_generate_reference_frequency_insights__mutmut_10, 
    'x_generate_reference_frequency_insights__mutmut_11': x_generate_reference_frequency_insights__mutmut_11, 
    'x_generate_reference_frequency_insights__mutmut_12': x_generate_reference_frequency_insights__mutmut_12, 
    'x_generate_reference_frequency_insights__mutmut_13': x_generate_reference_frequency_insights__mutmut_13, 
    'x_generate_reference_frequency_insights__mutmut_14': x_generate_reference_frequency_insights__mutmut_14, 
    'x_generate_reference_frequency_insights__mutmut_15': x_generate_reference_frequency_insights__mutmut_15, 
    'x_generate_reference_frequency_insights__mutmut_16': x_generate_reference_frequency_insights__mutmut_16, 
    'x_generate_reference_frequency_insights__mutmut_17': x_generate_reference_frequency_insights__mutmut_17, 
    'x_generate_reference_frequency_insights__mutmut_18': x_generate_reference_frequency_insights__mutmut_18, 
    'x_generate_reference_frequency_insights__mutmut_19': x_generate_reference_frequency_insights__mutmut_19, 
    'x_generate_reference_frequency_insights__mutmut_20': x_generate_reference_frequency_insights__mutmut_20, 
    'x_generate_reference_frequency_insights__mutmut_21': x_generate_reference_frequency_insights__mutmut_21
}
x_generate_reference_frequency_insights__mutmut_orig.__name__ = 'x_generate_reference_frequency_insights'


# -----------------------------------------------------------------------------

def generate_reference_type_insights(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    args = [patterns, threshold]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_generate_reference_type_insights__mutmut_orig, x_generate_reference_type_insights__mutmut_mutants, args, kwargs, None)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_orig(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_type_frequency",
                        "reference_type": ref_type,
                        "count": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_1(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = None

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_type_frequency",
                        "reference_type": ref_type,
                        "count": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_2(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = None

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_type_frequency",
                        "reference_type": ref_type,
                        "count": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_3(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(None)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_type_frequency",
                        "reference_type": ref_type,
                        "count": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_4(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count >= threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_type_frequency",
                        "reference_type": ref_type,
                        "count": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_5(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                None
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_6(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    None
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_7(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "XXtypeXX": "hypothesis",
                        "category": "reference_type_frequency",
                        "reference_type": ref_type,
                        "count": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_8(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "TYPE": "hypothesis",
                        "category": "reference_type_frequency",
                        "reference_type": ref_type,
                        "count": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_9(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "XXhypothesisXX",
                        "category": "reference_type_frequency",
                        "reference_type": ref_type,
                        "count": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_10(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "HYPOTHESIS",
                        "category": "reference_type_frequency",
                        "reference_type": ref_type,
                        "count": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_11(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "XXcategoryXX": "reference_type_frequency",
                        "reference_type": ref_type,
                        "count": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_12(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "CATEGORY": "reference_type_frequency",
                        "reference_type": ref_type,
                        "count": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_13(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "XXreference_type_frequencyXX",
                        "reference_type": ref_type,
                        "count": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_14(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "REFERENCE_TYPE_FREQUENCY",
                        "reference_type": ref_type,
                        "count": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_15(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_type_frequency",
                        "XXreference_typeXX": ref_type,
                        "count": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_16(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_type_frequency",
                        "REFERENCE_TYPE": ref_type,
                        "count": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_17(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_type_frequency",
                        "reference_type": ref_type,
                        "XXcountXX": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_18(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_type_frequency",
                        "reference_type": ref_type,
                        "COUNT": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_19(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_type_frequency",
                        "reference_type": ref_type,
                        "count": count,
                        "XXstatementXX": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_20(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_type_frequency",
                        "reference_type": ref_type,
                        "count": count,
                        "STATEMENT": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(insights)


# -----------------------------------------------------------------------------

def x_generate_reference_type_insights__mutmut_21(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate insights from governance type frequency.
    """

    insights: List[Dict[str, object]] = []

    freq_map = _safe_type_frequency_map(patterns)

    for ref_type, count in freq_map.items():
        if count > threshold:
            insights.append(
                _build_insight(
                    {
                        "type": "hypothesis",
                        "category": "reference_type_frequency",
                        "reference_type": ref_type,
                        "count": count,
                        "statement": (
                            f"{ref_type} references appear frequently across "
                            f"observed executions ({count} times)."
                        ),
                    }
                )
            )

    return tuple(None)

x_generate_reference_type_insights__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_generate_reference_type_insights__mutmut_1': x_generate_reference_type_insights__mutmut_1, 
    'x_generate_reference_type_insights__mutmut_2': x_generate_reference_type_insights__mutmut_2, 
    'x_generate_reference_type_insights__mutmut_3': x_generate_reference_type_insights__mutmut_3, 
    'x_generate_reference_type_insights__mutmut_4': x_generate_reference_type_insights__mutmut_4, 
    'x_generate_reference_type_insights__mutmut_5': x_generate_reference_type_insights__mutmut_5, 
    'x_generate_reference_type_insights__mutmut_6': x_generate_reference_type_insights__mutmut_6, 
    'x_generate_reference_type_insights__mutmut_7': x_generate_reference_type_insights__mutmut_7, 
    'x_generate_reference_type_insights__mutmut_8': x_generate_reference_type_insights__mutmut_8, 
    'x_generate_reference_type_insights__mutmut_9': x_generate_reference_type_insights__mutmut_9, 
    'x_generate_reference_type_insights__mutmut_10': x_generate_reference_type_insights__mutmut_10, 
    'x_generate_reference_type_insights__mutmut_11': x_generate_reference_type_insights__mutmut_11, 
    'x_generate_reference_type_insights__mutmut_12': x_generate_reference_type_insights__mutmut_12, 
    'x_generate_reference_type_insights__mutmut_13': x_generate_reference_type_insights__mutmut_13, 
    'x_generate_reference_type_insights__mutmut_14': x_generate_reference_type_insights__mutmut_14, 
    'x_generate_reference_type_insights__mutmut_15': x_generate_reference_type_insights__mutmut_15, 
    'x_generate_reference_type_insights__mutmut_16': x_generate_reference_type_insights__mutmut_16, 
    'x_generate_reference_type_insights__mutmut_17': x_generate_reference_type_insights__mutmut_17, 
    'x_generate_reference_type_insights__mutmut_18': x_generate_reference_type_insights__mutmut_18, 
    'x_generate_reference_type_insights__mutmut_19': x_generate_reference_type_insights__mutmut_19, 
    'x_generate_reference_type_insights__mutmut_20': x_generate_reference_type_insights__mutmut_20, 
    'x_generate_reference_type_insights__mutmut_21': x_generate_reference_type_insights__mutmut_21
}
x_generate_reference_type_insights__mutmut_orig.__name__ = 'x_generate_reference_type_insights'


# =============================================================================
# AGGREGATION
# =============================================================================

def generate_insights(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    args = [patterns, threshold]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_generate_insights__mutmut_orig, x_generate_insights__mutmut_mutants, args, kwargs, None)


# =============================================================================
# AGGREGATION
# =============================================================================

def x_generate_insights__mutmut_orig(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate all AFRIPower insights.

    ✅ Aggregated
    ✅ Deterministic ordering preserved
    """

    return (
        *generate_reference_frequency_insights(patterns, threshold),
        *generate_reference_type_insights(patterns, threshold),
    )


# =============================================================================
# AGGREGATION
# =============================================================================

def x_generate_insights__mutmut_1(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate all AFRIPower insights.

    ✅ Aggregated
    ✅ Deterministic ordering preserved
    """

    return (
        *generate_reference_frequency_insights(None, threshold),
        *generate_reference_type_insights(patterns, threshold),
    )


# =============================================================================
# AGGREGATION
# =============================================================================

def x_generate_insights__mutmut_2(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate all AFRIPower insights.

    ✅ Aggregated
    ✅ Deterministic ordering preserved
    """

    return (
        *generate_reference_frequency_insights(patterns, None),
        *generate_reference_type_insights(patterns, threshold),
    )


# =============================================================================
# AGGREGATION
# =============================================================================

def x_generate_insights__mutmut_3(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate all AFRIPower insights.

    ✅ Aggregated
    ✅ Deterministic ordering preserved
    """

    return (
        *generate_reference_frequency_insights(threshold),
        *generate_reference_type_insights(patterns, threshold),
    )


# =============================================================================
# AGGREGATION
# =============================================================================

def x_generate_insights__mutmut_4(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate all AFRIPower insights.

    ✅ Aggregated
    ✅ Deterministic ordering preserved
    """

    return (
        *generate_reference_frequency_insights(patterns, ),
        *generate_reference_type_insights(patterns, threshold),
    )


# =============================================================================
# AGGREGATION
# =============================================================================

def x_generate_insights__mutmut_5(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate all AFRIPower insights.

    ✅ Aggregated
    ✅ Deterministic ordering preserved
    """

    return (
        *generate_reference_frequency_insights(patterns, threshold),
        *generate_reference_type_insights(None, threshold),
    )


# =============================================================================
# AGGREGATION
# =============================================================================

def x_generate_insights__mutmut_6(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate all AFRIPower insights.

    ✅ Aggregated
    ✅ Deterministic ordering preserved
    """

    return (
        *generate_reference_frequency_insights(patterns, threshold),
        *generate_reference_type_insights(patterns, None),
    )


# =============================================================================
# AGGREGATION
# =============================================================================

def x_generate_insights__mutmut_7(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate all AFRIPower insights.

    ✅ Aggregated
    ✅ Deterministic ordering preserved
    """

    return (
        *generate_reference_frequency_insights(patterns, threshold),
        *generate_reference_type_insights(threshold),
    )


# =============================================================================
# AGGREGATION
# =============================================================================

def x_generate_insights__mutmut_8(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Tuple[Dict[str, object], ...]:
    """
    Generate all AFRIPower insights.

    ✅ Aggregated
    ✅ Deterministic ordering preserved
    """

    return (
        *generate_reference_frequency_insights(patterns, threshold),
        *generate_reference_type_insights(patterns, ),
    )

x_generate_insights__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_generate_insights__mutmut_1': x_generate_insights__mutmut_1, 
    'x_generate_insights__mutmut_2': x_generate_insights__mutmut_2, 
    'x_generate_insights__mutmut_3': x_generate_insights__mutmut_3, 
    'x_generate_insights__mutmut_4': x_generate_insights__mutmut_4, 
    'x_generate_insights__mutmut_5': x_generate_insights__mutmut_5, 
    'x_generate_insights__mutmut_6': x_generate_insights__mutmut_6, 
    'x_generate_insights__mutmut_7': x_generate_insights__mutmut_7, 
    'x_generate_insights__mutmut_8': x_generate_insights__mutmut_8
}
x_generate_insights__mutmut_orig.__name__ = 'x_generate_insights'


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def build_insight_payload(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    args = [patterns, threshold]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_insight_payload__mutmut_orig, x_build_insight_payload__mutmut_mutants, args, kwargs, None)


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_orig(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_1(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = None

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_2(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(None, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_3(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, None)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_4(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_5(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, )

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_6(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "XXstatusXX": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_7(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "STATUS": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_8(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "XXREAD_ONLYXX",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_9(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "read_only",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_10(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "XXreasoning_statusXX": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_11(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "REASONING_STATUS": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_12(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "XXinsight_classificationXX": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_13(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "INSIGHT_CLASSIFICATION": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_14(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "XXread_onlyXX": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_15(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "READ_ONLY": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_16(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "XXdisplay_onlyXX": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_17(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "DISPLAY_ONLY": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_18(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "XXobservational_onlyXX": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_19(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "OBSERVATIONAL_ONLY": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_20(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "XXinterpretive_onlyXX": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_21(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "INTERPRETIVE_ONLY": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_22(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "XXauthoritativeXX": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_23(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "AUTHORITATIVE": False,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_24(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": True,

        # outputs
        "insight_count": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_25(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "XXinsight_countXX": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_26(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "INSIGHT_COUNT": len(insights),
        "insights": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_27(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "XXinsightsXX": insights,
    }


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def x_build_insight_payload__mutmut_28(
    patterns: Mapping[str, Any],
    threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> Dict[str, object]:
    """
    Build canonical AFRIPower insight payload.

    ✅ Safe for dashboards / APIs
    ✅ Non-authoritative
    ✅ Deterministic
    """

    insights = generate_insights(patterns, threshold)

    return {
        "status": "READ_ONLY",
        "reasoning_status": REASONING_STATUS,
        "insight_classification": INSIGHT_CLASSIFICATION,

        # flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,

        "authoritative": False,

        # outputs
        "insight_count": len(insights),
        "INSIGHTS": insights,
    }

x_build_insight_payload__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_insight_payload__mutmut_1': x_build_insight_payload__mutmut_1, 
    'x_build_insight_payload__mutmut_2': x_build_insight_payload__mutmut_2, 
    'x_build_insight_payload__mutmut_3': x_build_insight_payload__mutmut_3, 
    'x_build_insight_payload__mutmut_4': x_build_insight_payload__mutmut_4, 
    'x_build_insight_payload__mutmut_5': x_build_insight_payload__mutmut_5, 
    'x_build_insight_payload__mutmut_6': x_build_insight_payload__mutmut_6, 
    'x_build_insight_payload__mutmut_7': x_build_insight_payload__mutmut_7, 
    'x_build_insight_payload__mutmut_8': x_build_insight_payload__mutmut_8, 
    'x_build_insight_payload__mutmut_9': x_build_insight_payload__mutmut_9, 
    'x_build_insight_payload__mutmut_10': x_build_insight_payload__mutmut_10, 
    'x_build_insight_payload__mutmut_11': x_build_insight_payload__mutmut_11, 
    'x_build_insight_payload__mutmut_12': x_build_insight_payload__mutmut_12, 
    'x_build_insight_payload__mutmut_13': x_build_insight_payload__mutmut_13, 
    'x_build_insight_payload__mutmut_14': x_build_insight_payload__mutmut_14, 
    'x_build_insight_payload__mutmut_15': x_build_insight_payload__mutmut_15, 
    'x_build_insight_payload__mutmut_16': x_build_insight_payload__mutmut_16, 
    'x_build_insight_payload__mutmut_17': x_build_insight_payload__mutmut_17, 
    'x_build_insight_payload__mutmut_18': x_build_insight_payload__mutmut_18, 
    'x_build_insight_payload__mutmut_19': x_build_insight_payload__mutmut_19, 
    'x_build_insight_payload__mutmut_20': x_build_insight_payload__mutmut_20, 
    'x_build_insight_payload__mutmut_21': x_build_insight_payload__mutmut_21, 
    'x_build_insight_payload__mutmut_22': x_build_insight_payload__mutmut_22, 
    'x_build_insight_payload__mutmut_23': x_build_insight_payload__mutmut_23, 
    'x_build_insight_payload__mutmut_24': x_build_insight_payload__mutmut_24, 
    'x_build_insight_payload__mutmut_25': x_build_insight_payload__mutmut_25, 
    'x_build_insight_payload__mutmut_26': x_build_insight_payload__mutmut_26, 
    'x_build_insight_payload__mutmut_27': x_build_insight_payload__mutmut_27, 
    'x_build_insight_payload__mutmut_28': x_build_insight_payload__mutmut_28
}
x_build_insight_payload__mutmut_orig.__name__ = 'x_build_insight_payload'


# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    "generate_reference_frequency_insights",
    "generate_reference_type_insights",
    "generate_insights",
    "build_insight_payload",
]