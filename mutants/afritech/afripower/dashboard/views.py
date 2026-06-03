"""
AFRIPower Dashboard Views

Read-only dashboard API surface.

This module MUST NEVER:
- execute runtime behavior
- validate truth
- enforce governance
- mutate receipts
- mutate proof artifacts
- create authority
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Dict, Tuple

# -----------------------------------------------------------------------------
# Optional DRF support
# -----------------------------------------------------------------------------

try:
    from rest_framework.response import Response
    from rest_framework.views import APIView
except Exception:  # pragma: no cover
    Response = None  # type: ignore[assignment]
    APIView = object  # type: ignore[assignment,misc]


from afritech.afripower.dashboard.constants import (
    DASHBOARD_STATUS,
    DISPLAY_ONLY,
    OBSERVATIONAL_ONLY,
    READ_ONLY,
)

from afritech.afripower.dashboard.services import (
    build_dashboard_payload,
)

from afritech.explainability.store import ExecutionExplanationStore
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
# INTERNAL HELPERS
# =============================================================================


def _empty_store() -> ExecutionExplanationStore:
    args = []# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__empty_store__mutmut_orig, x__empty_store__mutmut_mutants, args, kwargs, None)

# =============================================================================
# INTERNAL HELPERS
# =============================================================================


def x__empty_store__mutmut_orig() -> ExecutionExplanationStore:
    """Return an empty read-only explanation store."""

    return ExecutionExplanationStore(records=())

# =============================================================================
# INTERNAL HELPERS
# =============================================================================


def x__empty_store__mutmut_1() -> ExecutionExplanationStore:
    """Return an empty read-only explanation store."""

    return ExecutionExplanationStore(records=None)

x__empty_store__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__empty_store__mutmut_1': x__empty_store__mutmut_1
}
x__empty_store__mutmut_orig.__name__ = 'x__empty_store'


def _safe_iterable(value: Any) -> Tuple[Mapping[str, Any], ...]:
    args = [value]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__safe_iterable__mutmut_orig, x__safe_iterable__mutmut_mutants, args, kwargs, None)


def x__safe_iterable__mutmut_orig(value: Any) -> Tuple[Mapping[str, Any], ...]:
    """
    Normalize iterable input safely.

    ✅ No mutation
    ✅ Defensive filtering
    """

    if not isinstance(value, Iterable):
        return ()

    result = []
    for item in value:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x__safe_iterable__mutmut_1(value: Any) -> Tuple[Mapping[str, Any], ...]:
    """
    Normalize iterable input safely.

    ✅ No mutation
    ✅ Defensive filtering
    """

    if isinstance(value, Iterable):
        return ()

    result = []
    for item in value:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x__safe_iterable__mutmut_2(value: Any) -> Tuple[Mapping[str, Any], ...]:
    """
    Normalize iterable input safely.

    ✅ No mutation
    ✅ Defensive filtering
    """

    if not isinstance(value, Iterable):
        return ()

    result = None
    for item in value:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(result)


def x__safe_iterable__mutmut_3(value: Any) -> Tuple[Mapping[str, Any], ...]:
    """
    Normalize iterable input safely.

    ✅ No mutation
    ✅ Defensive filtering
    """

    if not isinstance(value, Iterable):
        return ()

    result = []
    for item in value:
        if isinstance(item, Mapping):
            result.append(None)

    return tuple(result)


def x__safe_iterable__mutmut_4(value: Any) -> Tuple[Mapping[str, Any], ...]:
    """
    Normalize iterable input safely.

    ✅ No mutation
    ✅ Defensive filtering
    """

    if not isinstance(value, Iterable):
        return ()

    result = []
    for item in value:
        if isinstance(item, Mapping):
            result.append(item)

    return tuple(None)

x__safe_iterable__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__safe_iterable__mutmut_1': x__safe_iterable__mutmut_1, 
    'x__safe_iterable__mutmut_2': x__safe_iterable__mutmut_2, 
    'x__safe_iterable__mutmut_3': x__safe_iterable__mutmut_3, 
    'x__safe_iterable__mutmut_4': x__safe_iterable__mutmut_4
}
x__safe_iterable__mutmut_orig.__name__ = 'x__safe_iterable'


def _store_from_request(request: Any) -> ExecutionExplanationStore:
    args = [request]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__store_from_request__mutmut_orig, x__store_from_request__mutmut_mutants, args, kwargs, None)


def x__store_from_request__mutmut_orig(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, "explanation_store", None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, "explanation_records", ())
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_1(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = None
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, "explanation_records", ())
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_2(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(None, "explanation_store", None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, "explanation_records", ())
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_3(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, None, None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, "explanation_records", ())
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_4(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr("explanation_store", None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, "explanation_records", ())
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_5(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, "explanation_records", ())
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_6(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, "explanation_store", )
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, "explanation_records", ())
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_7(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, "XXexplanation_storeXX", None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, "explanation_records", ())
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_8(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, "EXPLANATION_STORE", None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, "explanation_records", ())
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_9(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, "explanation_store", None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = None
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_10(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, "explanation_store", None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(None, "explanation_records", ())
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_11(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, "explanation_store", None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, None, ())
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_12(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, "explanation_store", None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, "explanation_records", None)
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_13(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, "explanation_store", None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr("explanation_records", ())
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_14(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, "explanation_store", None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, ())
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_15(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, "explanation_store", None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, "explanation_records", )
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_16(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, "explanation_store", None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, "XXexplanation_recordsXX", ())
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_17(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, "explanation_store", None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, "EXPLANATION_RECORDS", ())
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_18(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, "explanation_store", None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, "explanation_records", ())
    safe_records = None

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_19(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, "explanation_store", None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, "explanation_records", ())
    safe_records = _safe_iterable(None)

    if safe_records:
        return ExecutionExplanationStore(records=safe_records)

    return _empty_store()


def x__store_from_request__mutmut_20(request: Any) -> ExecutionExplanationStore:
    """
    Resolve a read-only explanation store from the request.

    ✅ Dependency-injected
    ✅ No runtime coupling
    ✅ No proof/replay/governance access
    """

    # Direct injection
    store = getattr(request, "explanation_store", None)
    if isinstance(store, ExecutionExplanationStore):
        return store

    # Raw records injection
    records = getattr(request, "explanation_records", ())
    safe_records = _safe_iterable(records)

    if safe_records:
        return ExecutionExplanationStore(records=None)

    return _empty_store()

x__store_from_request__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__store_from_request__mutmut_1': x__store_from_request__mutmut_1, 
    'x__store_from_request__mutmut_2': x__store_from_request__mutmut_2, 
    'x__store_from_request__mutmut_3': x__store_from_request__mutmut_3, 
    'x__store_from_request__mutmut_4': x__store_from_request__mutmut_4, 
    'x__store_from_request__mutmut_5': x__store_from_request__mutmut_5, 
    'x__store_from_request__mutmut_6': x__store_from_request__mutmut_6, 
    'x__store_from_request__mutmut_7': x__store_from_request__mutmut_7, 
    'x__store_from_request__mutmut_8': x__store_from_request__mutmut_8, 
    'x__store_from_request__mutmut_9': x__store_from_request__mutmut_9, 
    'x__store_from_request__mutmut_10': x__store_from_request__mutmut_10, 
    'x__store_from_request__mutmut_11': x__store_from_request__mutmut_11, 
    'x__store_from_request__mutmut_12': x__store_from_request__mutmut_12, 
    'x__store_from_request__mutmut_13': x__store_from_request__mutmut_13, 
    'x__store_from_request__mutmut_14': x__store_from_request__mutmut_14, 
    'x__store_from_request__mutmut_15': x__store_from_request__mutmut_15, 
    'x__store_from_request__mutmut_16': x__store_from_request__mutmut_16, 
    'x__store_from_request__mutmut_17': x__store_from_request__mutmut_17, 
    'x__store_from_request__mutmut_18': x__store_from_request__mutmut_18, 
    'x__store_from_request__mutmut_19': x__store_from_request__mutmut_19, 
    'x__store_from_request__mutmut_20': x__store_from_request__mutmut_20
}
x__store_from_request__mutmut_orig.__name__ = 'x__store_from_request'


def _with_dashboard_boundary(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    args = [payload]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__with_dashboard_boundary__mutmut_orig, x__with_dashboard_boundary__mutmut_mutants, args, kwargs, None)


def x__with_dashboard_boundary__mutmut_orig(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_1(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = None

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_2(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(None)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_3(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "XXdashboard_statusXX": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_4(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "DASHBOARD_STATUS": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_5(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "XXread_onlyXX": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_6(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "READ_ONLY": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_7(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "XXdisplay_onlyXX": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_8(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "DISPLAY_ONLY": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_9(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "XXobservational_onlyXX": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_10(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "OBSERVATIONAL_ONLY": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_11(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "XXruntime_authorityXX": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_12(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "RUNTIME_AUTHORITY": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_13(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": True,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_14(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "XXvalidation_authorityXX": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_15(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "VALIDATION_AUTHORITY": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_16(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": True,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_17(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "XXgovernance_authorityXX": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_18(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "GOVERNANCE_AUTHORITY": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_19(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": True,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_20(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "XXenforcement_authorityXX": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_21(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "ENFORCEMENT_AUTHORITY": False,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_22(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": True,
        "replay_authority": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_23(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "XXreplay_authorityXX": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_24(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "REPLAY_AUTHORITY": False,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_25(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": True,
        "proof_authority": False,
    }


def x__with_dashboard_boundary__mutmut_26(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "XXproof_authorityXX": False,
    }


def x__with_dashboard_boundary__mutmut_27(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "PROOF_AUTHORITY": False,
    }


def x__with_dashboard_boundary__mutmut_28(
    payload: Mapping[str, Any],
) -> Dict[str, object]:
    """
    Attach non-authority boundary metadata.

    ✅ No dict.update (validator-safe)
    ✅ Explicit authority fields
    """

    base = dict(payload)

    return {
        **base,

        # explicit dashboard boundary
        "dashboard_status": DASHBOARD_STATUS,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,

        # authority flags (STRICT FALSE)
        "runtime_authority": False,
        "validation_authority": False,
        "governance_authority": False,
        "enforcement_authority": False,
        "replay_authority": False,
        "proof_authority": True,
    }

x__with_dashboard_boundary__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__with_dashboard_boundary__mutmut_1': x__with_dashboard_boundary__mutmut_1, 
    'x__with_dashboard_boundary__mutmut_2': x__with_dashboard_boundary__mutmut_2, 
    'x__with_dashboard_boundary__mutmut_3': x__with_dashboard_boundary__mutmut_3, 
    'x__with_dashboard_boundary__mutmut_4': x__with_dashboard_boundary__mutmut_4, 
    'x__with_dashboard_boundary__mutmut_5': x__with_dashboard_boundary__mutmut_5, 
    'x__with_dashboard_boundary__mutmut_6': x__with_dashboard_boundary__mutmut_6, 
    'x__with_dashboard_boundary__mutmut_7': x__with_dashboard_boundary__mutmut_7, 
    'x__with_dashboard_boundary__mutmut_8': x__with_dashboard_boundary__mutmut_8, 
    'x__with_dashboard_boundary__mutmut_9': x__with_dashboard_boundary__mutmut_9, 
    'x__with_dashboard_boundary__mutmut_10': x__with_dashboard_boundary__mutmut_10, 
    'x__with_dashboard_boundary__mutmut_11': x__with_dashboard_boundary__mutmut_11, 
    'x__with_dashboard_boundary__mutmut_12': x__with_dashboard_boundary__mutmut_12, 
    'x__with_dashboard_boundary__mutmut_13': x__with_dashboard_boundary__mutmut_13, 
    'x__with_dashboard_boundary__mutmut_14': x__with_dashboard_boundary__mutmut_14, 
    'x__with_dashboard_boundary__mutmut_15': x__with_dashboard_boundary__mutmut_15, 
    'x__with_dashboard_boundary__mutmut_16': x__with_dashboard_boundary__mutmut_16, 
    'x__with_dashboard_boundary__mutmut_17': x__with_dashboard_boundary__mutmut_17, 
    'x__with_dashboard_boundary__mutmut_18': x__with_dashboard_boundary__mutmut_18, 
    'x__with_dashboard_boundary__mutmut_19': x__with_dashboard_boundary__mutmut_19, 
    'x__with_dashboard_boundary__mutmut_20': x__with_dashboard_boundary__mutmut_20, 
    'x__with_dashboard_boundary__mutmut_21': x__with_dashboard_boundary__mutmut_21, 
    'x__with_dashboard_boundary__mutmut_22': x__with_dashboard_boundary__mutmut_22, 
    'x__with_dashboard_boundary__mutmut_23': x__with_dashboard_boundary__mutmut_23, 
    'x__with_dashboard_boundary__mutmut_24': x__with_dashboard_boundary__mutmut_24, 
    'x__with_dashboard_boundary__mutmut_25': x__with_dashboard_boundary__mutmut_25, 
    'x__with_dashboard_boundary__mutmut_26': x__with_dashboard_boundary__mutmut_26, 
    'x__with_dashboard_boundary__mutmut_27': x__with_dashboard_boundary__mutmut_27, 
    'x__with_dashboard_boundary__mutmut_28': x__with_dashboard_boundary__mutmut_28
}
x__with_dashboard_boundary__mutmut_orig.__name__ = 'x__with_dashboard_boundary'


def _build_payload_from_store(
    store: ExecutionExplanationStore,
) -> Dict[str, object]:
    args = [store]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__build_payload_from_store__mutmut_orig, x__build_payload_from_store__mutmut_mutants, args, kwargs, None)


def x__build_payload_from_store__mutmut_orig(
    store: ExecutionExplanationStore,
) -> Dict[str, object]:
    """
    Build dashboard payload from store.

    ✅ Read-only
    ✅ No mutation
    """

    receipts = store.receipts()
    payload = build_dashboard_payload(receipts)

    return _with_dashboard_boundary(payload)


def x__build_payload_from_store__mutmut_1(
    store: ExecutionExplanationStore,
) -> Dict[str, object]:
    """
    Build dashboard payload from store.

    ✅ Read-only
    ✅ No mutation
    """

    receipts = None
    payload = build_dashboard_payload(receipts)

    return _with_dashboard_boundary(payload)


def x__build_payload_from_store__mutmut_2(
    store: ExecutionExplanationStore,
) -> Dict[str, object]:
    """
    Build dashboard payload from store.

    ✅ Read-only
    ✅ No mutation
    """

    receipts = store.receipts()
    payload = None

    return _with_dashboard_boundary(payload)


def x__build_payload_from_store__mutmut_3(
    store: ExecutionExplanationStore,
) -> Dict[str, object]:
    """
    Build dashboard payload from store.

    ✅ Read-only
    ✅ No mutation
    """

    receipts = store.receipts()
    payload = build_dashboard_payload(None)

    return _with_dashboard_boundary(payload)


def x__build_payload_from_store__mutmut_4(
    store: ExecutionExplanationStore,
) -> Dict[str, object]:
    """
    Build dashboard payload from store.

    ✅ Read-only
    ✅ No mutation
    """

    receipts = store.receipts()
    payload = build_dashboard_payload(receipts)

    return _with_dashboard_boundary(None)

x__build_payload_from_store__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__build_payload_from_store__mutmut_1': x__build_payload_from_store__mutmut_1, 
    'x__build_payload_from_store__mutmut_2': x__build_payload_from_store__mutmut_2, 
    'x__build_payload_from_store__mutmut_3': x__build_payload_from_store__mutmut_3, 
    'x__build_payload_from_store__mutmut_4': x__build_payload_from_store__mutmut_4
}
x__build_payload_from_store__mutmut_orig.__name__ = 'x__build_payload_from_store'


# =============================================================================
# API VIEW
# =============================================================================


class AFRIPowerDashboardView(APIView):
    """
    Read-only AFRIPower dashboard endpoint.

    ❗ Outputs are:
        - observational
        - interpretive
        - non-authoritative

    ❗ Outputs MUST NOT be used for:
        - admissibility decisions
        - validation decisions
        - runtime decisions
        - governance enforcement
    """

    def get(self, request: Any) -> Any:
        args = [request]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁAFRIPowerDashboardViewǁget__mutmut_orig'), object.__getattribute__(self, 'xǁAFRIPowerDashboardViewǁget__mutmut_mutants'), args, kwargs, self)

    def xǁAFRIPowerDashboardViewǁget__mutmut_orig(self, request: Any) -> Any:
        """
        GET dashboard payload.

        ✅ Safe
        ✅ Deterministic
        ✅ Read-only
        """

        store = _store_from_request(request)
        payload = _build_payload_from_store(store)

        if Response is None:  # pragma: no cover
            return payload

        return Response(payload)

    def xǁAFRIPowerDashboardViewǁget__mutmut_1(self, request: Any) -> Any:
        """
        GET dashboard payload.

        ✅ Safe
        ✅ Deterministic
        ✅ Read-only
        """

        store = None
        payload = _build_payload_from_store(store)

        if Response is None:  # pragma: no cover
            return payload

        return Response(payload)

    def xǁAFRIPowerDashboardViewǁget__mutmut_2(self, request: Any) -> Any:
        """
        GET dashboard payload.

        ✅ Safe
        ✅ Deterministic
        ✅ Read-only
        """

        store = _store_from_request(None)
        payload = _build_payload_from_store(store)

        if Response is None:  # pragma: no cover
            return payload

        return Response(payload)

    def xǁAFRIPowerDashboardViewǁget__mutmut_3(self, request: Any) -> Any:
        """
        GET dashboard payload.

        ✅ Safe
        ✅ Deterministic
        ✅ Read-only
        """

        store = _store_from_request(request)
        payload = None

        if Response is None:  # pragma: no cover
            return payload

        return Response(payload)

    def xǁAFRIPowerDashboardViewǁget__mutmut_4(self, request: Any) -> Any:
        """
        GET dashboard payload.

        ✅ Safe
        ✅ Deterministic
        ✅ Read-only
        """

        store = _store_from_request(request)
        payload = _build_payload_from_store(None)

        if Response is None:  # pragma: no cover
            return payload

        return Response(payload)

    def xǁAFRIPowerDashboardViewǁget__mutmut_5(self, request: Any) -> Any:
        """
        GET dashboard payload.

        ✅ Safe
        ✅ Deterministic
        ✅ Read-only
        """

        store = _store_from_request(request)
        payload = _build_payload_from_store(store)

        if Response is not None:  # pragma: no cover
            return payload

        return Response(payload)

    def xǁAFRIPowerDashboardViewǁget__mutmut_6(self, request: Any) -> Any:
        """
        GET dashboard payload.

        ✅ Safe
        ✅ Deterministic
        ✅ Read-only
        """

        store = _store_from_request(request)
        payload = _build_payload_from_store(store)

        if Response is None:  # pragma: no cover
            return payload

        return Response(None)
    
    xǁAFRIPowerDashboardViewǁget__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁAFRIPowerDashboardViewǁget__mutmut_1': xǁAFRIPowerDashboardViewǁget__mutmut_1, 
        'xǁAFRIPowerDashboardViewǁget__mutmut_2': xǁAFRIPowerDashboardViewǁget__mutmut_2, 
        'xǁAFRIPowerDashboardViewǁget__mutmut_3': xǁAFRIPowerDashboardViewǁget__mutmut_3, 
        'xǁAFRIPowerDashboardViewǁget__mutmut_4': xǁAFRIPowerDashboardViewǁget__mutmut_4, 
        'xǁAFRIPowerDashboardViewǁget__mutmut_5': xǁAFRIPowerDashboardViewǁget__mutmut_5, 
        'xǁAFRIPowerDashboardViewǁget__mutmut_6': xǁAFRIPowerDashboardViewǁget__mutmut_6
    }
    xǁAFRIPowerDashboardViewǁget__mutmut_orig.__name__ = 'xǁAFRIPowerDashboardViewǁget'


# =============================================================================
# NON-DRF HELPERS
# =============================================================================


def build_dashboard_response_from_receipts(
    receipts: Iterable[Mapping[str, Any]],
) -> Dict[str, object]:
    args = [receipts]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_dashboard_response_from_receipts__mutmut_orig, x_build_dashboard_response_from_receipts__mutmut_mutants, args, kwargs, None)


# =============================================================================
# NON-DRF HELPERS
# =============================================================================


def x_build_dashboard_response_from_receipts__mutmut_orig(
    receipts: Iterable[Mapping[str, Any]],
) -> Dict[str, object]:
    """
    Helper for:
        - tests
        - CLI tools
        - scripts

    ✅ Pure
    ✅ No mutation
    ✅ No framework dependency
    """

    safe_receipts = _safe_iterable(receipts)
    payload = build_dashboard_payload(safe_receipts)

    return _with_dashboard_boundary(payload)


# =============================================================================
# NON-DRF HELPERS
# =============================================================================


def x_build_dashboard_response_from_receipts__mutmut_1(
    receipts: Iterable[Mapping[str, Any]],
) -> Dict[str, object]:
    """
    Helper for:
        - tests
        - CLI tools
        - scripts

    ✅ Pure
    ✅ No mutation
    ✅ No framework dependency
    """

    safe_receipts = None
    payload = build_dashboard_payload(safe_receipts)

    return _with_dashboard_boundary(payload)


# =============================================================================
# NON-DRF HELPERS
# =============================================================================


def x_build_dashboard_response_from_receipts__mutmut_2(
    receipts: Iterable[Mapping[str, Any]],
) -> Dict[str, object]:
    """
    Helper for:
        - tests
        - CLI tools
        - scripts

    ✅ Pure
    ✅ No mutation
    ✅ No framework dependency
    """

    safe_receipts = _safe_iterable(None)
    payload = build_dashboard_payload(safe_receipts)

    return _with_dashboard_boundary(payload)


# =============================================================================
# NON-DRF HELPERS
# =============================================================================


def x_build_dashboard_response_from_receipts__mutmut_3(
    receipts: Iterable[Mapping[str, Any]],
) -> Dict[str, object]:
    """
    Helper for:
        - tests
        - CLI tools
        - scripts

    ✅ Pure
    ✅ No mutation
    ✅ No framework dependency
    """

    safe_receipts = _safe_iterable(receipts)
    payload = None

    return _with_dashboard_boundary(payload)


# =============================================================================
# NON-DRF HELPERS
# =============================================================================


def x_build_dashboard_response_from_receipts__mutmut_4(
    receipts: Iterable[Mapping[str, Any]],
) -> Dict[str, object]:
    """
    Helper for:
        - tests
        - CLI tools
        - scripts

    ✅ Pure
    ✅ No mutation
    ✅ No framework dependency
    """

    safe_receipts = _safe_iterable(receipts)
    payload = build_dashboard_payload(None)

    return _with_dashboard_boundary(payload)


# =============================================================================
# NON-DRF HELPERS
# =============================================================================


def x_build_dashboard_response_from_receipts__mutmut_5(
    receipts: Iterable[Mapping[str, Any]],
) -> Dict[str, object]:
    """
    Helper for:
        - tests
        - CLI tools
        - scripts

    ✅ Pure
    ✅ No mutation
    ✅ No framework dependency
    """

    safe_receipts = _safe_iterable(receipts)
    payload = build_dashboard_payload(safe_receipts)

    return _with_dashboard_boundary(None)

x_build_dashboard_response_from_receipts__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_dashboard_response_from_receipts__mutmut_1': x_build_dashboard_response_from_receipts__mutmut_1, 
    'x_build_dashboard_response_from_receipts__mutmut_2': x_build_dashboard_response_from_receipts__mutmut_2, 
    'x_build_dashboard_response_from_receipts__mutmut_3': x_build_dashboard_response_from_receipts__mutmut_3, 
    'x_build_dashboard_response_from_receipts__mutmut_4': x_build_dashboard_response_from_receipts__mutmut_4, 
    'x_build_dashboard_response_from_receipts__mutmut_5': x_build_dashboard_response_from_receipts__mutmut_5
}
x_build_dashboard_response_from_receipts__mutmut_orig.__name__ = 'x_build_dashboard_response_from_receipts'


def build_dashboard_response_from_store(
    store: ExecutionExplanationStore,
) -> Dict[str, object]:
    args = [store]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_dashboard_response_from_store__mutmut_orig, x_build_dashboard_response_from_store__mutmut_mutants, args, kwargs, None)


def x_build_dashboard_response_from_store__mutmut_orig(
    store: ExecutionExplanationStore,
) -> Dict[str, object]:
    """
    Build payload directly from store.

    ✅ Useful for service-layer usage
    """

    if not isinstance(store, ExecutionExplanationStore):
        return _build_payload_from_store(_empty_store())

    return _build_payload_from_store(store)


def x_build_dashboard_response_from_store__mutmut_1(
    store: ExecutionExplanationStore,
) -> Dict[str, object]:
    """
    Build payload directly from store.

    ✅ Useful for service-layer usage
    """

    if isinstance(store, ExecutionExplanationStore):
        return _build_payload_from_store(_empty_store())

    return _build_payload_from_store(store)


def x_build_dashboard_response_from_store__mutmut_2(
    store: ExecutionExplanationStore,
) -> Dict[str, object]:
    """
    Build payload directly from store.

    ✅ Useful for service-layer usage
    """

    if not isinstance(store, ExecutionExplanationStore):
        return _build_payload_from_store(None)

    return _build_payload_from_store(store)


def x_build_dashboard_response_from_store__mutmut_3(
    store: ExecutionExplanationStore,
) -> Dict[str, object]:
    """
    Build payload directly from store.

    ✅ Useful for service-layer usage
    """

    if not isinstance(store, ExecutionExplanationStore):
        return _build_payload_from_store(_empty_store())

    return _build_payload_from_store(None)

x_build_dashboard_response_from_store__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_dashboard_response_from_store__mutmut_1': x_build_dashboard_response_from_store__mutmut_1, 
    'x_build_dashboard_response_from_store__mutmut_2': x_build_dashboard_response_from_store__mutmut_2, 
    'x_build_dashboard_response_from_store__mutmut_3': x_build_dashboard_response_from_store__mutmut_3
}
x_build_dashboard_response_from_store__mutmut_orig.__name__ = 'x_build_dashboard_response_from_store'


# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    "AFRIPowerDashboardView",
    "build_dashboard_response_from_receipts",
    "build_dashboard_response_from_store",
]