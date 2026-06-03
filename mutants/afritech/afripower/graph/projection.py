"""
AFRIPower Graph Projection — Read-Only Representation Layer
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Dict, Tuple, List, Set

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

Receipt = Mapping[str, Any]
GraphNodeDict = Dict[str, object]
GraphEdgeDict = Dict[str, object]
GraphDict = Dict[str, object]

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


def _safe_get_refs(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    args = [receipt]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__safe_get_refs__mutmut_orig, x__safe_get_refs__mutmut_mutants, args, kwargs, None)


def x__safe_get_refs__mutmut_orig(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_1(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = None
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_2(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(None)
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_3(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(None, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_4(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, None))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_5(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_6(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_7(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = None

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_8(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_9(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            break

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_10(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = None
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_11(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).upper()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_12(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(None).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_13(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get(None)).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_14(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("XXtypeXX")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_15(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("TYPE")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_16(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = None

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_17(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(None)

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_18(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get(None))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_19(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("XXidXX"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_20(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("ID"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_21(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type or ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_22(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append(None)

    return tuple(refs)


def x__safe_get_refs__mutmut_23(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"XXtypeXX": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_24(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"TYPE": ref_type, "id": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_25(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "XXidXX": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_26(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "ID": ref_id})

    return tuple(refs)


def x__safe_get_refs__mutmut_27(receipt: Receipt) -> Tuple[Dict[str, str], ...]:
    """
    Extract governance references safely.

    ✅ Defensive
    ✅ Deterministic
    ✅ No mutation
    """

    raw = _safe_sequence(receipt.get(_TRACEABILITY_KEY, ()))
    refs: List[Dict[str, str]] = []

    for item in raw:
        if not isinstance(item, Mapping):
            continue

        ref_type = _safe_str(item.get("type")).lower()
        ref_id = _safe_str(item.get("id"))

        if ref_type and ref_id:
            refs.append({"type": ref_type, "id": ref_id})

    return tuple(None)

x__safe_get_refs__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__safe_get_refs__mutmut_1': x__safe_get_refs__mutmut_1, 
    'x__safe_get_refs__mutmut_2': x__safe_get_refs__mutmut_2, 
    'x__safe_get_refs__mutmut_3': x__safe_get_refs__mutmut_3, 
    'x__safe_get_refs__mutmut_4': x__safe_get_refs__mutmut_4, 
    'x__safe_get_refs__mutmut_5': x__safe_get_refs__mutmut_5, 
    'x__safe_get_refs__mutmut_6': x__safe_get_refs__mutmut_6, 
    'x__safe_get_refs__mutmut_7': x__safe_get_refs__mutmut_7, 
    'x__safe_get_refs__mutmut_8': x__safe_get_refs__mutmut_8, 
    'x__safe_get_refs__mutmut_9': x__safe_get_refs__mutmut_9, 
    'x__safe_get_refs__mutmut_10': x__safe_get_refs__mutmut_10, 
    'x__safe_get_refs__mutmut_11': x__safe_get_refs__mutmut_11, 
    'x__safe_get_refs__mutmut_12': x__safe_get_refs__mutmut_12, 
    'x__safe_get_refs__mutmut_13': x__safe_get_refs__mutmut_13, 
    'x__safe_get_refs__mutmut_14': x__safe_get_refs__mutmut_14, 
    'x__safe_get_refs__mutmut_15': x__safe_get_refs__mutmut_15, 
    'x__safe_get_refs__mutmut_16': x__safe_get_refs__mutmut_16, 
    'x__safe_get_refs__mutmut_17': x__safe_get_refs__mutmut_17, 
    'x__safe_get_refs__mutmut_18': x__safe_get_refs__mutmut_18, 
    'x__safe_get_refs__mutmut_19': x__safe_get_refs__mutmut_19, 
    'x__safe_get_refs__mutmut_20': x__safe_get_refs__mutmut_20, 
    'x__safe_get_refs__mutmut_21': x__safe_get_refs__mutmut_21, 
    'x__safe_get_refs__mutmut_22': x__safe_get_refs__mutmut_22, 
    'x__safe_get_refs__mutmut_23': x__safe_get_refs__mutmut_23, 
    'x__safe_get_refs__mutmut_24': x__safe_get_refs__mutmut_24, 
    'x__safe_get_refs__mutmut_25': x__safe_get_refs__mutmut_25, 
    'x__safe_get_refs__mutmut_26': x__safe_get_refs__mutmut_26, 
    'x__safe_get_refs__mutmut_27': x__safe_get_refs__mutmut_27
}
x__safe_get_refs__mutmut_orig.__name__ = 'x__safe_get_refs'


# =============================================================================
# NODE / EDGE NORMALIZATION
# =============================================================================

def _node_key(node_type: str, node_id: str) -> Tuple[str, str]:
    args = [node_type, node_id]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__node_key__mutmut_orig, x__node_key__mutmut_mutants, args, kwargs, None)


# =============================================================================
# NODE / EDGE NORMALIZATION
# =============================================================================

def x__node_key__mutmut_orig(node_type: str, node_id: str) -> Tuple[str, str]:
    return (_safe_str(node_type), _safe_str(node_id))


# =============================================================================
# NODE / EDGE NORMALIZATION
# =============================================================================

def x__node_key__mutmut_1(node_type: str, node_id: str) -> Tuple[str, str]:
    return (_safe_str(None), _safe_str(node_id))


# =============================================================================
# NODE / EDGE NORMALIZATION
# =============================================================================

def x__node_key__mutmut_2(node_type: str, node_id: str) -> Tuple[str, str]:
    return (_safe_str(node_type), _safe_str(None))

x__node_key__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__node_key__mutmut_1': x__node_key__mutmut_1, 
    'x__node_key__mutmut_2': x__node_key__mutmut_2
}
x__node_key__mutmut_orig.__name__ = 'x__node_key'


def _unique_nodes(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    args = [nodes]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__unique_nodes__mutmut_orig, x__unique_nodes__mutmut_mutants, args, kwargs, None)


def x__unique_nodes__mutmut_orig(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_1(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = None
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_2(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = None

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_3(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = None
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_4(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(None, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_5(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, None)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_6(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_7(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, )
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_8(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] and not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_9(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_10(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[1] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_11(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_12(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[2]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_13(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            break

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_14(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_15(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(None)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_16(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                None
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_17(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "XXidXX": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_18(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "ID": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_19(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[2],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_20(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "XXtypeXX": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_21(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "TYPE": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_22(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[1],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_23(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "XXread_onlyXX": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_24(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "READ_ONLY": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_25(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "XXdisplay_onlyXX": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_26(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "DISPLAY_ONLY": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_27(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "XXobservational_onlyXX": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_28(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "OBSERVATIONAL_ONLY": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_29(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "XXrepresentation_onlyXX": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_30(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "REPRESENTATION_ONLY": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_31(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "XXauthoritativeXX": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_32(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "AUTHORITATIVE": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_33(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": True,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_34(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(None)


def x__unique_nodes__mutmut_35(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(None, key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_36(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=None))


def x__unique_nodes__mutmut_37(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(key=lambda n: (n["type"], n["id"])))


def x__unique_nodes__mutmut_38(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, ))


def x__unique_nodes__mutmut_39(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: None))


def x__unique_nodes__mutmut_40(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["XXtypeXX"], n["id"])))


def x__unique_nodes__mutmut_41(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["TYPE"], n["id"])))


def x__unique_nodes__mutmut_42(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["XXidXX"])))


def x__unique_nodes__mutmut_43(nodes: Iterable[Tuple[str, str]]) -> Tuple[GraphNodeDict, ...]:
    """
    Deduplicate nodes deterministically.
    """

    seen: Set[Tuple[str, str]] = set()
    result: List[GraphNodeDict] = []

    for node_type, node_id in nodes:
        key = _node_key(node_type, node_id)
        if not key[0] or not key[1]:
            continue

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "id": key[1],
                    "type": key[0],
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(sorted(result, key=lambda n: (n["type"], n["ID"])))

x__unique_nodes__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__unique_nodes__mutmut_1': x__unique_nodes__mutmut_1, 
    'x__unique_nodes__mutmut_2': x__unique_nodes__mutmut_2, 
    'x__unique_nodes__mutmut_3': x__unique_nodes__mutmut_3, 
    'x__unique_nodes__mutmut_4': x__unique_nodes__mutmut_4, 
    'x__unique_nodes__mutmut_5': x__unique_nodes__mutmut_5, 
    'x__unique_nodes__mutmut_6': x__unique_nodes__mutmut_6, 
    'x__unique_nodes__mutmut_7': x__unique_nodes__mutmut_7, 
    'x__unique_nodes__mutmut_8': x__unique_nodes__mutmut_8, 
    'x__unique_nodes__mutmut_9': x__unique_nodes__mutmut_9, 
    'x__unique_nodes__mutmut_10': x__unique_nodes__mutmut_10, 
    'x__unique_nodes__mutmut_11': x__unique_nodes__mutmut_11, 
    'x__unique_nodes__mutmut_12': x__unique_nodes__mutmut_12, 
    'x__unique_nodes__mutmut_13': x__unique_nodes__mutmut_13, 
    'x__unique_nodes__mutmut_14': x__unique_nodes__mutmut_14, 
    'x__unique_nodes__mutmut_15': x__unique_nodes__mutmut_15, 
    'x__unique_nodes__mutmut_16': x__unique_nodes__mutmut_16, 
    'x__unique_nodes__mutmut_17': x__unique_nodes__mutmut_17, 
    'x__unique_nodes__mutmut_18': x__unique_nodes__mutmut_18, 
    'x__unique_nodes__mutmut_19': x__unique_nodes__mutmut_19, 
    'x__unique_nodes__mutmut_20': x__unique_nodes__mutmut_20, 
    'x__unique_nodes__mutmut_21': x__unique_nodes__mutmut_21, 
    'x__unique_nodes__mutmut_22': x__unique_nodes__mutmut_22, 
    'x__unique_nodes__mutmut_23': x__unique_nodes__mutmut_23, 
    'x__unique_nodes__mutmut_24': x__unique_nodes__mutmut_24, 
    'x__unique_nodes__mutmut_25': x__unique_nodes__mutmut_25, 
    'x__unique_nodes__mutmut_26': x__unique_nodes__mutmut_26, 
    'x__unique_nodes__mutmut_27': x__unique_nodes__mutmut_27, 
    'x__unique_nodes__mutmut_28': x__unique_nodes__mutmut_28, 
    'x__unique_nodes__mutmut_29': x__unique_nodes__mutmut_29, 
    'x__unique_nodes__mutmut_30': x__unique_nodes__mutmut_30, 
    'x__unique_nodes__mutmut_31': x__unique_nodes__mutmut_31, 
    'x__unique_nodes__mutmut_32': x__unique_nodes__mutmut_32, 
    'x__unique_nodes__mutmut_33': x__unique_nodes__mutmut_33, 
    'x__unique_nodes__mutmut_34': x__unique_nodes__mutmut_34, 
    'x__unique_nodes__mutmut_35': x__unique_nodes__mutmut_35, 
    'x__unique_nodes__mutmut_36': x__unique_nodes__mutmut_36, 
    'x__unique_nodes__mutmut_37': x__unique_nodes__mutmut_37, 
    'x__unique_nodes__mutmut_38': x__unique_nodes__mutmut_38, 
    'x__unique_nodes__mutmut_39': x__unique_nodes__mutmut_39, 
    'x__unique_nodes__mutmut_40': x__unique_nodes__mutmut_40, 
    'x__unique_nodes__mutmut_41': x__unique_nodes__mutmut_41, 
    'x__unique_nodes__mutmut_42': x__unique_nodes__mutmut_42, 
    'x__unique_nodes__mutmut_43': x__unique_nodes__mutmut_43
}
x__unique_nodes__mutmut_orig.__name__ = 'x__unique_nodes'


def _unique_edges(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    args = [edges]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__unique_edges__mutmut_orig, x__unique_edges__mutmut_mutants, args, kwargs, None)


def x__unique_edges__mutmut_orig(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_1(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = None
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_2(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = None

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_3(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = None
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_4(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(None)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_5(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = None
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_6(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(None)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_7(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = None

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_8(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(None)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_9(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t and not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_10(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s and not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_11(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_12(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_13(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_14(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            break

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_15(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = None

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_16(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_17(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(None)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_18(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                None
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_19(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "XXfromXX": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_20(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "FROM": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_21(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "XXtoXX": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_22(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "TO": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_23(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "XXrelationXX": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_24(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "RELATION": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_25(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "XXread_onlyXX": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_26(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "READ_ONLY": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_27(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "XXdisplay_onlyXX": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_28(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "DISPLAY_ONLY": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_29(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "XXobservational_onlyXX": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_30(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "OBSERVATIONAL_ONLY": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_31(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "XXrepresentation_onlyXX": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_32(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "REPRESENTATION_ONLY": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_33(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "XXauthoritativeXX": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_34(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "AUTHORITATIVE": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_35(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": True,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_36(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        None
    )


def x__unique_edges__mutmut_37(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(None, key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_38(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=None)
    )


def x__unique_edges__mutmut_39(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(key=lambda e: (e["from"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_40(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, )
    )


def x__unique_edges__mutmut_41(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: None)
    )


def x__unique_edges__mutmut_42(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["XXfromXX"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_43(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["FROM"], e["to"], e["relation"]))
    )


def x__unique_edges__mutmut_44(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["XXtoXX"], e["relation"]))
    )


def x__unique_edges__mutmut_45(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["TO"], e["relation"]))
    )


def x__unique_edges__mutmut_46(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["XXrelationXX"]))
    )


def x__unique_edges__mutmut_47(
    edges: Iterable[Tuple[str, str, str]],
) -> Tuple[GraphEdgeDict, ...]:
    """
    Deduplicate + normalize edges.
    """

    seen: Set[Tuple[str, str, str]] = set()
    result: List[GraphEdgeDict] = []

    for source, target, relation in edges:
        s = _safe_str(source)
        t = _safe_str(target)
        r = _safe_str(relation)

        if not s or not t or not r:
            continue

        key = (s, t, r)

        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "from": s,
                    "to": t,
                    "relation": r,
                    "read_only": READ_ONLY,
                    "display_only": DISPLAY_ONLY,
                    "observational_only": OBSERVATIONAL_ONLY,
                    "representation_only": REPRESENTATION_ONLY,
                    "authoritative": False,
                }
            )

    return tuple(
        sorted(result, key=lambda e: (e["from"], e["to"], e["RELATION"]))
    )

x__unique_edges__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__unique_edges__mutmut_1': x__unique_edges__mutmut_1, 
    'x__unique_edges__mutmut_2': x__unique_edges__mutmut_2, 
    'x__unique_edges__mutmut_3': x__unique_edges__mutmut_3, 
    'x__unique_edges__mutmut_4': x__unique_edges__mutmut_4, 
    'x__unique_edges__mutmut_5': x__unique_edges__mutmut_5, 
    'x__unique_edges__mutmut_6': x__unique_edges__mutmut_6, 
    'x__unique_edges__mutmut_7': x__unique_edges__mutmut_7, 
    'x__unique_edges__mutmut_8': x__unique_edges__mutmut_8, 
    'x__unique_edges__mutmut_9': x__unique_edges__mutmut_9, 
    'x__unique_edges__mutmut_10': x__unique_edges__mutmut_10, 
    'x__unique_edges__mutmut_11': x__unique_edges__mutmut_11, 
    'x__unique_edges__mutmut_12': x__unique_edges__mutmut_12, 
    'x__unique_edges__mutmut_13': x__unique_edges__mutmut_13, 
    'x__unique_edges__mutmut_14': x__unique_edges__mutmut_14, 
    'x__unique_edges__mutmut_15': x__unique_edges__mutmut_15, 
    'x__unique_edges__mutmut_16': x__unique_edges__mutmut_16, 
    'x__unique_edges__mutmut_17': x__unique_edges__mutmut_17, 
    'x__unique_edges__mutmut_18': x__unique_edges__mutmut_18, 
    'x__unique_edges__mutmut_19': x__unique_edges__mutmut_19, 
    'x__unique_edges__mutmut_20': x__unique_edges__mutmut_20, 
    'x__unique_edges__mutmut_21': x__unique_edges__mutmut_21, 
    'x__unique_edges__mutmut_22': x__unique_edges__mutmut_22, 
    'x__unique_edges__mutmut_23': x__unique_edges__mutmut_23, 
    'x__unique_edges__mutmut_24': x__unique_edges__mutmut_24, 
    'x__unique_edges__mutmut_25': x__unique_edges__mutmut_25, 
    'x__unique_edges__mutmut_26': x__unique_edges__mutmut_26, 
    'x__unique_edges__mutmut_27': x__unique_edges__mutmut_27, 
    'x__unique_edges__mutmut_28': x__unique_edges__mutmut_28, 
    'x__unique_edges__mutmut_29': x__unique_edges__mutmut_29, 
    'x__unique_edges__mutmut_30': x__unique_edges__mutmut_30, 
    'x__unique_edges__mutmut_31': x__unique_edges__mutmut_31, 
    'x__unique_edges__mutmut_32': x__unique_edges__mutmut_32, 
    'x__unique_edges__mutmut_33': x__unique_edges__mutmut_33, 
    'x__unique_edges__mutmut_34': x__unique_edges__mutmut_34, 
    'x__unique_edges__mutmut_35': x__unique_edges__mutmut_35, 
    'x__unique_edges__mutmut_36': x__unique_edges__mutmut_36, 
    'x__unique_edges__mutmut_37': x__unique_edges__mutmut_37, 
    'x__unique_edges__mutmut_38': x__unique_edges__mutmut_38, 
    'x__unique_edges__mutmut_39': x__unique_edges__mutmut_39, 
    'x__unique_edges__mutmut_40': x__unique_edges__mutmut_40, 
    'x__unique_edges__mutmut_41': x__unique_edges__mutmut_41, 
    'x__unique_edges__mutmut_42': x__unique_edges__mutmut_42, 
    'x__unique_edges__mutmut_43': x__unique_edges__mutmut_43, 
    'x__unique_edges__mutmut_44': x__unique_edges__mutmut_44, 
    'x__unique_edges__mutmut_45': x__unique_edges__mutmut_45, 
    'x__unique_edges__mutmut_46': x__unique_edges__mutmut_46, 
    'x__unique_edges__mutmut_47': x__unique_edges__mutmut_47
}
x__unique_edges__mutmut_orig.__name__ = 'x__unique_edges'


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def project_graph(receipts: Iterable[Receipt]) -> GraphDict:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_project_graph__mutmut_orig, x_project_graph__mutmut_mutants, args, kwargs, None)


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_orig(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_1(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = None

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_2(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = None
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_3(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = None

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_4(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = None
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_5(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 1
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_6(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = None

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_7(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 1

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_8(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = None
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_9(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(None)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_10(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_11(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            break

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_12(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count = 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_13(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count -= 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_14(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 2
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_15(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(None)

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_16(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("XXexecutionXX", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_17(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("EXECUTION", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_18(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(None):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_19(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = None
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_20(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["XXtypeXX"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_21(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["TYPE"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_22(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = None

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_23(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["XXidXX"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_24(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["ID"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_25(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count = 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_26(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count -= 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_27(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 2

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_28(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append(None)
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_29(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append(None)

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_30(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "XXreferencesXX"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_31(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "REFERENCES"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_32(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = None
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_33(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(None)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_34(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = None

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_35(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(None)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_36(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_37(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_38(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_39(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_40(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_41(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_42(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_43(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_44(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_45(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_46(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_47(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_48(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_49(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_50(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_51(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_52(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_53(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "XXnodesXX": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_54(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "NODES": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_55(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(None),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_56(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "XXedgesXX": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_57(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "EDGES": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_58(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(None),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_59(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "XXmetadataXX": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_60(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "METADATA": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_61(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "XXexecution_countXX": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_62(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "EXECUTION_COUNT": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_63(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "XXreference_countXX": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_64(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "REFERENCE_COUNT": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_65(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "XXnode_countXX": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_66(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "NODE_COUNT": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_67(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "XXedge_countXX": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_68(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "EDGE_COUNT": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_69(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "XXreceipt_count_observedXX": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_70(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "RECEIPT_COUNT_OBSERVED": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_71(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "XXrepresentation_onlyXX": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_72(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "REPRESENTATION_ONLY": REPRESENTATION_ONLY,
            "authoritative": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_73(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "XXauthoritativeXX": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_74(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "AUTHORITATIVE": False,
        },
    }


# =============================================================================
# MAIN PROJECTION
# =============================================================================

def x_project_graph__mutmut_75(receipts: Iterable[Receipt]) -> GraphDict:
    """
    Build read-only AFRIPower graph.

    ✅ Deterministic
    ✅ Pure
    ✅ Non-authoritative
    """

    receipt_list: List[Receipt] = [
        r for r in receipts if isinstance(r, Mapping)
    ]

    node_stream: List[Tuple[str, str]] = []
    edge_stream: List[Tuple[str, str, str]] = []

    execution_count = 0
    reference_count = 0

    for receipt in receipt_list:
        execution_id = _safe_execution_id(receipt)
        if not execution_id:
            continue

        execution_count += 1
        node_stream.append(("execution", execution_id))

        for ref in _safe_get_refs(receipt):
            ref_type = ref["type"]
            ref_id = ref["id"]

            reference_count += 1

            node_stream.append((ref_type, ref_id))
            edge_stream.append((execution_id, ref_id, "references"))

    nodes = _unique_nodes(node_stream)
    edges = _unique_edges(edge_stream)

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

        # data
        "nodes": list(nodes),
        "edges": list(edges),

        # metadata
        "metadata": {
            "execution_count": execution_count,
            "reference_count": reference_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "receipt_count_observed": len(receipt_list),

            # safety
            "representation_only": REPRESENTATION_ONLY,
            "authoritative": True,
        },
    }

x_project_graph__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_project_graph__mutmut_1': x_project_graph__mutmut_1, 
    'x_project_graph__mutmut_2': x_project_graph__mutmut_2, 
    'x_project_graph__mutmut_3': x_project_graph__mutmut_3, 
    'x_project_graph__mutmut_4': x_project_graph__mutmut_4, 
    'x_project_graph__mutmut_5': x_project_graph__mutmut_5, 
    'x_project_graph__mutmut_6': x_project_graph__mutmut_6, 
    'x_project_graph__mutmut_7': x_project_graph__mutmut_7, 
    'x_project_graph__mutmut_8': x_project_graph__mutmut_8, 
    'x_project_graph__mutmut_9': x_project_graph__mutmut_9, 
    'x_project_graph__mutmut_10': x_project_graph__mutmut_10, 
    'x_project_graph__mutmut_11': x_project_graph__mutmut_11, 
    'x_project_graph__mutmut_12': x_project_graph__mutmut_12, 
    'x_project_graph__mutmut_13': x_project_graph__mutmut_13, 
    'x_project_graph__mutmut_14': x_project_graph__mutmut_14, 
    'x_project_graph__mutmut_15': x_project_graph__mutmut_15, 
    'x_project_graph__mutmut_16': x_project_graph__mutmut_16, 
    'x_project_graph__mutmut_17': x_project_graph__mutmut_17, 
    'x_project_graph__mutmut_18': x_project_graph__mutmut_18, 
    'x_project_graph__mutmut_19': x_project_graph__mutmut_19, 
    'x_project_graph__mutmut_20': x_project_graph__mutmut_20, 
    'x_project_graph__mutmut_21': x_project_graph__mutmut_21, 
    'x_project_graph__mutmut_22': x_project_graph__mutmut_22, 
    'x_project_graph__mutmut_23': x_project_graph__mutmut_23, 
    'x_project_graph__mutmut_24': x_project_graph__mutmut_24, 
    'x_project_graph__mutmut_25': x_project_graph__mutmut_25, 
    'x_project_graph__mutmut_26': x_project_graph__mutmut_26, 
    'x_project_graph__mutmut_27': x_project_graph__mutmut_27, 
    'x_project_graph__mutmut_28': x_project_graph__mutmut_28, 
    'x_project_graph__mutmut_29': x_project_graph__mutmut_29, 
    'x_project_graph__mutmut_30': x_project_graph__mutmut_30, 
    'x_project_graph__mutmut_31': x_project_graph__mutmut_31, 
    'x_project_graph__mutmut_32': x_project_graph__mutmut_32, 
    'x_project_graph__mutmut_33': x_project_graph__mutmut_33, 
    'x_project_graph__mutmut_34': x_project_graph__mutmut_34, 
    'x_project_graph__mutmut_35': x_project_graph__mutmut_35, 
    'x_project_graph__mutmut_36': x_project_graph__mutmut_36, 
    'x_project_graph__mutmut_37': x_project_graph__mutmut_37, 
    'x_project_graph__mutmut_38': x_project_graph__mutmut_38, 
    'x_project_graph__mutmut_39': x_project_graph__mutmut_39, 
    'x_project_graph__mutmut_40': x_project_graph__mutmut_40, 
    'x_project_graph__mutmut_41': x_project_graph__mutmut_41, 
    'x_project_graph__mutmut_42': x_project_graph__mutmut_42, 
    'x_project_graph__mutmut_43': x_project_graph__mutmut_43, 
    'x_project_graph__mutmut_44': x_project_graph__mutmut_44, 
    'x_project_graph__mutmut_45': x_project_graph__mutmut_45, 
    'x_project_graph__mutmut_46': x_project_graph__mutmut_46, 
    'x_project_graph__mutmut_47': x_project_graph__mutmut_47, 
    'x_project_graph__mutmut_48': x_project_graph__mutmut_48, 
    'x_project_graph__mutmut_49': x_project_graph__mutmut_49, 
    'x_project_graph__mutmut_50': x_project_graph__mutmut_50, 
    'x_project_graph__mutmut_51': x_project_graph__mutmut_51, 
    'x_project_graph__mutmut_52': x_project_graph__mutmut_52, 
    'x_project_graph__mutmut_53': x_project_graph__mutmut_53, 
    'x_project_graph__mutmut_54': x_project_graph__mutmut_54, 
    'x_project_graph__mutmut_55': x_project_graph__mutmut_55, 
    'x_project_graph__mutmut_56': x_project_graph__mutmut_56, 
    'x_project_graph__mutmut_57': x_project_graph__mutmut_57, 
    'x_project_graph__mutmut_58': x_project_graph__mutmut_58, 
    'x_project_graph__mutmut_59': x_project_graph__mutmut_59, 
    'x_project_graph__mutmut_60': x_project_graph__mutmut_60, 
    'x_project_graph__mutmut_61': x_project_graph__mutmut_61, 
    'x_project_graph__mutmut_62': x_project_graph__mutmut_62, 
    'x_project_graph__mutmut_63': x_project_graph__mutmut_63, 
    'x_project_graph__mutmut_64': x_project_graph__mutmut_64, 
    'x_project_graph__mutmut_65': x_project_graph__mutmut_65, 
    'x_project_graph__mutmut_66': x_project_graph__mutmut_66, 
    'x_project_graph__mutmut_67': x_project_graph__mutmut_67, 
    'x_project_graph__mutmut_68': x_project_graph__mutmut_68, 
    'x_project_graph__mutmut_69': x_project_graph__mutmut_69, 
    'x_project_graph__mutmut_70': x_project_graph__mutmut_70, 
    'x_project_graph__mutmut_71': x_project_graph__mutmut_71, 
    'x_project_graph__mutmut_72': x_project_graph__mutmut_72, 
    'x_project_graph__mutmut_73': x_project_graph__mutmut_73, 
    'x_project_graph__mutmut_74': x_project_graph__mutmut_74, 
    'x_project_graph__mutmut_75': x_project_graph__mutmut_75
}
x_project_graph__mutmut_orig.__name__ = 'x_project_graph'


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def extract_execution_nodes(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    args = [graph]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_extract_execution_nodes__mutmut_orig, x_extract_execution_nodes__mutmut_mutants, args, kwargs, None)


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_orig(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") == "execution"
    )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_1(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = None
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") == "execution"
    )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_2(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = graph.get(None, ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") == "execution"
    )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_3(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = graph.get("nodes", None)
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") == "execution"
    )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_4(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = graph.get(())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") == "execution"
    )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_5(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = graph.get("nodes", )
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") == "execution"
    )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_6(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = graph.get("XXnodesXX", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") == "execution"
    )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_7(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = graph.get("NODES", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") == "execution"
    )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_8(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = graph.get("nodes", ())
    if isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") == "execution"
    )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_9(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        None
    )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_10(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(None)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") == "execution"
    )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_11(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) or n.get("type") == "execution"
    )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_12(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get(None) == "execution"
    )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_13(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("XXtypeXX") == "execution"
    )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_14(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("TYPE") == "execution"
    )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_15(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") != "execution"
    )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_16(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") == "XXexecutionXX"
    )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def x_extract_execution_nodes__mutmut_17(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return execution nodes only."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") == "EXECUTION"
    )

x_extract_execution_nodes__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_extract_execution_nodes__mutmut_1': x_extract_execution_nodes__mutmut_1, 
    'x_extract_execution_nodes__mutmut_2': x_extract_execution_nodes__mutmut_2, 
    'x_extract_execution_nodes__mutmut_3': x_extract_execution_nodes__mutmut_3, 
    'x_extract_execution_nodes__mutmut_4': x_extract_execution_nodes__mutmut_4, 
    'x_extract_execution_nodes__mutmut_5': x_extract_execution_nodes__mutmut_5, 
    'x_extract_execution_nodes__mutmut_6': x_extract_execution_nodes__mutmut_6, 
    'x_extract_execution_nodes__mutmut_7': x_extract_execution_nodes__mutmut_7, 
    'x_extract_execution_nodes__mutmut_8': x_extract_execution_nodes__mutmut_8, 
    'x_extract_execution_nodes__mutmut_9': x_extract_execution_nodes__mutmut_9, 
    'x_extract_execution_nodes__mutmut_10': x_extract_execution_nodes__mutmut_10, 
    'x_extract_execution_nodes__mutmut_11': x_extract_execution_nodes__mutmut_11, 
    'x_extract_execution_nodes__mutmut_12': x_extract_execution_nodes__mutmut_12, 
    'x_extract_execution_nodes__mutmut_13': x_extract_execution_nodes__mutmut_13, 
    'x_extract_execution_nodes__mutmut_14': x_extract_execution_nodes__mutmut_14, 
    'x_extract_execution_nodes__mutmut_15': x_extract_execution_nodes__mutmut_15, 
    'x_extract_execution_nodes__mutmut_16': x_extract_execution_nodes__mutmut_16, 
    'x_extract_execution_nodes__mutmut_17': x_extract_execution_nodes__mutmut_17
}
x_extract_execution_nodes__mutmut_orig.__name__ = 'x_extract_execution_nodes'


def extract_governance_nodes(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    args = [graph]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_extract_governance_nodes__mutmut_orig, x_extract_governance_nodes__mutmut_mutants, args, kwargs, None)


def x_extract_governance_nodes__mutmut_orig(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") != "execution"
    )


def x_extract_governance_nodes__mutmut_1(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = None
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") != "execution"
    )


def x_extract_governance_nodes__mutmut_2(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = graph.get(None, ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") != "execution"
    )


def x_extract_governance_nodes__mutmut_3(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = graph.get("nodes", None)
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") != "execution"
    )


def x_extract_governance_nodes__mutmut_4(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = graph.get(())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") != "execution"
    )


def x_extract_governance_nodes__mutmut_5(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = graph.get("nodes", )
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") != "execution"
    )


def x_extract_governance_nodes__mutmut_6(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = graph.get("XXnodesXX", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") != "execution"
    )


def x_extract_governance_nodes__mutmut_7(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = graph.get("NODES", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") != "execution"
    )


def x_extract_governance_nodes__mutmut_8(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = graph.get("nodes", ())
    if isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") != "execution"
    )


def x_extract_governance_nodes__mutmut_9(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        None
    )


def x_extract_governance_nodes__mutmut_10(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(None)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") != "execution"
    )


def x_extract_governance_nodes__mutmut_11(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) or n.get("type") != "execution"
    )


def x_extract_governance_nodes__mutmut_12(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get(None) != "execution"
    )


def x_extract_governance_nodes__mutmut_13(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("XXtypeXX") != "execution"
    )


def x_extract_governance_nodes__mutmut_14(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("TYPE") != "execution"
    )


def x_extract_governance_nodes__mutmut_15(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") == "execution"
    )


def x_extract_governance_nodes__mutmut_16(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") != "XXexecutionXX"
    )


def x_extract_governance_nodes__mutmut_17(graph: Mapping[str, Any]) -> Tuple[GraphNodeDict, ...]:
    """Return non-execution nodes."""

    nodes = graph.get("nodes", ())
    if not isinstance(nodes, Sequence):
        return ()

    return tuple(
        dict(n)
        for n in nodes
        if isinstance(n, Mapping) and n.get("type") != "EXECUTION"
    )

x_extract_governance_nodes__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_extract_governance_nodes__mutmut_1': x_extract_governance_nodes__mutmut_1, 
    'x_extract_governance_nodes__mutmut_2': x_extract_governance_nodes__mutmut_2, 
    'x_extract_governance_nodes__mutmut_3': x_extract_governance_nodes__mutmut_3, 
    'x_extract_governance_nodes__mutmut_4': x_extract_governance_nodes__mutmut_4, 
    'x_extract_governance_nodes__mutmut_5': x_extract_governance_nodes__mutmut_5, 
    'x_extract_governance_nodes__mutmut_6': x_extract_governance_nodes__mutmut_6, 
    'x_extract_governance_nodes__mutmut_7': x_extract_governance_nodes__mutmut_7, 
    'x_extract_governance_nodes__mutmut_8': x_extract_governance_nodes__mutmut_8, 
    'x_extract_governance_nodes__mutmut_9': x_extract_governance_nodes__mutmut_9, 
    'x_extract_governance_nodes__mutmut_10': x_extract_governance_nodes__mutmut_10, 
    'x_extract_governance_nodes__mutmut_11': x_extract_governance_nodes__mutmut_11, 
    'x_extract_governance_nodes__mutmut_12': x_extract_governance_nodes__mutmut_12, 
    'x_extract_governance_nodes__mutmut_13': x_extract_governance_nodes__mutmut_13, 
    'x_extract_governance_nodes__mutmut_14': x_extract_governance_nodes__mutmut_14, 
    'x_extract_governance_nodes__mutmut_15': x_extract_governance_nodes__mutmut_15, 
    'x_extract_governance_nodes__mutmut_16': x_extract_governance_nodes__mutmut_16, 
    'x_extract_governance_nodes__mutmut_17': x_extract_governance_nodes__mutmut_17
}
x_extract_governance_nodes__mutmut_orig.__name__ = 'x_extract_governance_nodes'


def extract_edges(graph: Mapping[str, Any]) -> Tuple[GraphEdgeDict, ...]:
    args = [graph]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_extract_edges__mutmut_orig, x_extract_edges__mutmut_mutants, args, kwargs, None)


def x_extract_edges__mutmut_orig(graph: Mapping[str, Any]) -> Tuple[GraphEdgeDict, ...]:
    """Return graph edges safely."""

    edges = graph.get("edges", ())
    if not isinstance(edges, Sequence):
        return ()

    return tuple(
        dict(e)
        for e in edges
        if isinstance(e, Mapping)
    )


def x_extract_edges__mutmut_1(graph: Mapping[str, Any]) -> Tuple[GraphEdgeDict, ...]:
    """Return graph edges safely."""

    edges = None
    if not isinstance(edges, Sequence):
        return ()

    return tuple(
        dict(e)
        for e in edges
        if isinstance(e, Mapping)
    )


def x_extract_edges__mutmut_2(graph: Mapping[str, Any]) -> Tuple[GraphEdgeDict, ...]:
    """Return graph edges safely."""

    edges = graph.get(None, ())
    if not isinstance(edges, Sequence):
        return ()

    return tuple(
        dict(e)
        for e in edges
        if isinstance(e, Mapping)
    )


def x_extract_edges__mutmut_3(graph: Mapping[str, Any]) -> Tuple[GraphEdgeDict, ...]:
    """Return graph edges safely."""

    edges = graph.get("edges", None)
    if not isinstance(edges, Sequence):
        return ()

    return tuple(
        dict(e)
        for e in edges
        if isinstance(e, Mapping)
    )


def x_extract_edges__mutmut_4(graph: Mapping[str, Any]) -> Tuple[GraphEdgeDict, ...]:
    """Return graph edges safely."""

    edges = graph.get(())
    if not isinstance(edges, Sequence):
        return ()

    return tuple(
        dict(e)
        for e in edges
        if isinstance(e, Mapping)
    )


def x_extract_edges__mutmut_5(graph: Mapping[str, Any]) -> Tuple[GraphEdgeDict, ...]:
    """Return graph edges safely."""

    edges = graph.get("edges", )
    if not isinstance(edges, Sequence):
        return ()

    return tuple(
        dict(e)
        for e in edges
        if isinstance(e, Mapping)
    )


def x_extract_edges__mutmut_6(graph: Mapping[str, Any]) -> Tuple[GraphEdgeDict, ...]:
    """Return graph edges safely."""

    edges = graph.get("XXedgesXX", ())
    if not isinstance(edges, Sequence):
        return ()

    return tuple(
        dict(e)
        for e in edges
        if isinstance(e, Mapping)
    )


def x_extract_edges__mutmut_7(graph: Mapping[str, Any]) -> Tuple[GraphEdgeDict, ...]:
    """Return graph edges safely."""

    edges = graph.get("EDGES", ())
    if not isinstance(edges, Sequence):
        return ()

    return tuple(
        dict(e)
        for e in edges
        if isinstance(e, Mapping)
    )


def x_extract_edges__mutmut_8(graph: Mapping[str, Any]) -> Tuple[GraphEdgeDict, ...]:
    """Return graph edges safely."""

    edges = graph.get("edges", ())
    if isinstance(edges, Sequence):
        return ()

    return tuple(
        dict(e)
        for e in edges
        if isinstance(e, Mapping)
    )


def x_extract_edges__mutmut_9(graph: Mapping[str, Any]) -> Tuple[GraphEdgeDict, ...]:
    """Return graph edges safely."""

    edges = graph.get("edges", ())
    if not isinstance(edges, Sequence):
        return ()

    return tuple(
        None
    )


def x_extract_edges__mutmut_10(graph: Mapping[str, Any]) -> Tuple[GraphEdgeDict, ...]:
    """Return graph edges safely."""

    edges = graph.get("edges", ())
    if not isinstance(edges, Sequence):
        return ()

    return tuple(
        dict(None)
        for e in edges
        if isinstance(e, Mapping)
    )

x_extract_edges__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_extract_edges__mutmut_1': x_extract_edges__mutmut_1, 
    'x_extract_edges__mutmut_2': x_extract_edges__mutmut_2, 
    'x_extract_edges__mutmut_3': x_extract_edges__mutmut_3, 
    'x_extract_edges__mutmut_4': x_extract_edges__mutmut_4, 
    'x_extract_edges__mutmut_5': x_extract_edges__mutmut_5, 
    'x_extract_edges__mutmut_6': x_extract_edges__mutmut_6, 
    'x_extract_edges__mutmut_7': x_extract_edges__mutmut_7, 
    'x_extract_edges__mutmut_8': x_extract_edges__mutmut_8, 
    'x_extract_edges__mutmut_9': x_extract_edges__mutmut_9, 
    'x_extract_edges__mutmut_10': x_extract_edges__mutmut_10
}
x_extract_edges__mutmut_orig.__name__ = 'x_extract_edges'


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def assert_projection_integrity(graph: Mapping[str, Any]) -> None:
    args = [graph]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_assert_projection_integrity__mutmut_orig, x_assert_projection_integrity__mutmut_mutants, args, kwargs, None)


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_orig(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("authoritative") is True:
        raise RuntimeError("Graph projection must not be authoritative")

    if graph.get("read_only") is not True:
        raise RuntimeError("Graph must remain read-only")


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_1(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get(None) is True:
        raise RuntimeError("Graph projection must not be authoritative")

    if graph.get("read_only") is not True:
        raise RuntimeError("Graph must remain read-only")


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_2(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("XXauthoritativeXX") is True:
        raise RuntimeError("Graph projection must not be authoritative")

    if graph.get("read_only") is not True:
        raise RuntimeError("Graph must remain read-only")


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_3(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("AUTHORITATIVE") is True:
        raise RuntimeError("Graph projection must not be authoritative")

    if graph.get("read_only") is not True:
        raise RuntimeError("Graph must remain read-only")


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_4(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("authoritative") is not True:
        raise RuntimeError("Graph projection must not be authoritative")

    if graph.get("read_only") is not True:
        raise RuntimeError("Graph must remain read-only")


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_5(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("authoritative") is False:
        raise RuntimeError("Graph projection must not be authoritative")

    if graph.get("read_only") is not True:
        raise RuntimeError("Graph must remain read-only")


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_6(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("authoritative") is True:
        raise RuntimeError(None)

    if graph.get("read_only") is not True:
        raise RuntimeError("Graph must remain read-only")


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_7(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("authoritative") is True:
        raise RuntimeError("XXGraph projection must not be authoritativeXX")

    if graph.get("read_only") is not True:
        raise RuntimeError("Graph must remain read-only")


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_8(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("authoritative") is True:
        raise RuntimeError("graph projection must not be authoritative")

    if graph.get("read_only") is not True:
        raise RuntimeError("Graph must remain read-only")


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_9(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("authoritative") is True:
        raise RuntimeError("GRAPH PROJECTION MUST NOT BE AUTHORITATIVE")

    if graph.get("read_only") is not True:
        raise RuntimeError("Graph must remain read-only")


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_10(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("authoritative") is True:
        raise RuntimeError("Graph projection must not be authoritative")

    if graph.get(None) is not True:
        raise RuntimeError("Graph must remain read-only")


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_11(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("authoritative") is True:
        raise RuntimeError("Graph projection must not be authoritative")

    if graph.get("XXread_onlyXX") is not True:
        raise RuntimeError("Graph must remain read-only")


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_12(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("authoritative") is True:
        raise RuntimeError("Graph projection must not be authoritative")

    if graph.get("READ_ONLY") is not True:
        raise RuntimeError("Graph must remain read-only")


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_13(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("authoritative") is True:
        raise RuntimeError("Graph projection must not be authoritative")

    if graph.get("read_only") is True:
        raise RuntimeError("Graph must remain read-only")


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_14(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("authoritative") is True:
        raise RuntimeError("Graph projection must not be authoritative")

    if graph.get("read_only") is not False:
        raise RuntimeError("Graph must remain read-only")


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_15(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("authoritative") is True:
        raise RuntimeError("Graph projection must not be authoritative")

    if graph.get("read_only") is not True:
        raise RuntimeError(None)


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_16(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("authoritative") is True:
        raise RuntimeError("Graph projection must not be authoritative")

    if graph.get("read_only") is not True:
        raise RuntimeError("XXGraph must remain read-onlyXX")


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_17(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("authoritative") is True:
        raise RuntimeError("Graph projection must not be authoritative")

    if graph.get("read_only") is not True:
        raise RuntimeError("graph must remain read-only")


# =============================================================================
# INTEGRITY CHECK
# =============================================================================

def x_assert_projection_integrity__mutmut_18(graph: Mapping[str, Any]) -> None:
    """
    Structural integrity check.

    ✅ No authority allowed
    """

    if graph.get("authoritative") is True:
        raise RuntimeError("Graph projection must not be authoritative")

    if graph.get("read_only") is not True:
        raise RuntimeError("GRAPH MUST REMAIN READ-ONLY")

x_assert_projection_integrity__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_assert_projection_integrity__mutmut_1': x_assert_projection_integrity__mutmut_1, 
    'x_assert_projection_integrity__mutmut_2': x_assert_projection_integrity__mutmut_2, 
    'x_assert_projection_integrity__mutmut_3': x_assert_projection_integrity__mutmut_3, 
    'x_assert_projection_integrity__mutmut_4': x_assert_projection_integrity__mutmut_4, 
    'x_assert_projection_integrity__mutmut_5': x_assert_projection_integrity__mutmut_5, 
    'x_assert_projection_integrity__mutmut_6': x_assert_projection_integrity__mutmut_6, 
    'x_assert_projection_integrity__mutmut_7': x_assert_projection_integrity__mutmut_7, 
    'x_assert_projection_integrity__mutmut_8': x_assert_projection_integrity__mutmut_8, 
    'x_assert_projection_integrity__mutmut_9': x_assert_projection_integrity__mutmut_9, 
    'x_assert_projection_integrity__mutmut_10': x_assert_projection_integrity__mutmut_10, 
    'x_assert_projection_integrity__mutmut_11': x_assert_projection_integrity__mutmut_11, 
    'x_assert_projection_integrity__mutmut_12': x_assert_projection_integrity__mutmut_12, 
    'x_assert_projection_integrity__mutmut_13': x_assert_projection_integrity__mutmut_13, 
    'x_assert_projection_integrity__mutmut_14': x_assert_projection_integrity__mutmut_14, 
    'x_assert_projection_integrity__mutmut_15': x_assert_projection_integrity__mutmut_15, 
    'x_assert_projection_integrity__mutmut_16': x_assert_projection_integrity__mutmut_16, 
    'x_assert_projection_integrity__mutmut_17': x_assert_projection_integrity__mutmut_17, 
    'x_assert_projection_integrity__mutmut_18': x_assert_projection_integrity__mutmut_18
}
x_assert_projection_integrity__mutmut_orig.__name__ = 'x_assert_projection_integrity'


# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    "project_graph",
    "extract_execution_nodes",
    "extract_governance_nodes",
    "extract_edges",
    "assert_projection_integrity",
]
