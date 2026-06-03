"""
AFRIPower Receipt Provider

Read-only adapter for supplying receipt-like records to AFRIPower
intelligence surfaces.

This module prevents AFRIPower from depending directly on:
    - runtime stores
    - proof stores
    - replay systems
    - execution services
    - governance projection stores

AFRIPower consumes receipt-like evidence snapshots.
AFRIPower does NOT:
    - create
    - validate
    - mutate
    - authorize

CONSTITUTIONAL GUARANTEES
------------------------
- Read-only
- Observational only
- Non-authoritative
- No mutation
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Tuple, Dict, List

# ✅ Correct import path (FIXED)
from afritech.afripower.contracts.read_only_contract  import (
    DEFAULT_READ_ONLY_CONTRACT,
    ReadOnlyContract,
    assert_read_only_contract,
)

# =============================================================================
# CONSTANTS (ALL NON-AUTHORITATIVE)
# =============================================================================

PROVIDER_STATUS = "READ_ONLY_RECEIPT_PROVIDER_V1"

RUNTIME_AUTHORITY = False
ENFORCEMENT_AUTHORITY = False
VALIDATION_AUTHORITY = False
GOVERNANCE_AUTHORITY = False
INTELLIGENCE_AUTHORITY = False

EXECUTION_AUTHORITY = False
REPLAY_AUTHORITY = False
PROOF_AUTHORITY = False

READ_ONLY = True
DISPLAY_ONLY = True
OBSERVATIONAL_ONLY = True

AUTHORITATIVE = False

Receipt = Mapping[str, Any]
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
# SNAPSHOT MODEL
# =============================================================================


@dataclass(frozen=True)
class ReceiptSnapshot:
    """
    Immutable receipt snapshot.

    ✅ Deep copied
    ✅ Observational only
    ✅ No authority
    """

    payload: Receipt = field(default_factory=dict)
    provider_status: str = PROVIDER_STATUS
    contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT

    def __post_init__(self) -> None:
        # Defensive normalization
        object.__setattr__(self, "payload", deepcopy(dict(self.payload)))

    def canonical_dict(self) -> Dict[str, object]:
        """Return safe, copied snapshot with metadata."""

        copied = deepcopy(dict(self.payload))

        return {
            **copied,

            # Provider metadata
            "provider_status": self.provider_status,

            # Authority flags (ALL FALSE)
            "runtime_authority": RUNTIME_AUTHORITY,
            "enforcement_authority": ENFORCEMENT_AUTHORITY,
            "validation_authority": VALIDATION_AUTHORITY,
            "governance_authority": GOVERNANCE_AUTHORITY,
            "intelligence_authority": INTELLIGENCE_AUTHORITY,
            "execution_authority": EXECUTION_AUTHORITY,
            "replay_authority": REPLAY_AUTHORITY,
            "proof_authority": PROOF_AUTHORITY,

            # Behavioral flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "observational_only": OBSERVATIONAL_ONLY,
            "authoritative": AUTHORITATIVE,
        }


# =============================================================================
# PROVIDER
# =============================================================================


class ReceiptProvider:
    """
    Read-only receipt provider.

    ❗ No mutation APIs
    ❗ No runtime linking
    ❗ No persistence

    ✅ Immutable internal storage
    ✅ Defensive normalization
    ✅ Contract enforcement
    """

    AUTHORITY = False

    def __init__(
        self,
        receipts: Iterable[ReceiptSnapshot | Receipt] = (),
        contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
    ) -> None:
        args = [receipts, contract]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁReceiptProviderǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁReceiptProviderǁ__init____mutmut_mutants'), args, kwargs, self)

    def xǁReceiptProviderǁ__init____mutmut_orig(
        self,
        receipts: Iterable[ReceiptSnapshot | Receipt] = (),
        contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
    ) -> None:

        if not assert_read_only_contract(contract):
            raise RuntimeError("Invalid AFRIPower contract supplied")

        self._contract: ReadOnlyContract = contract

        self._receipts: Tuple[ReceiptSnapshot, ...] = tuple(
            self._normalize_receipt(r, contract)
            for r in receipts
        )

    def xǁReceiptProviderǁ__init____mutmut_1(
        self,
        receipts: Iterable[ReceiptSnapshot | Receipt] = (),
        contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
    ) -> None:

        if assert_read_only_contract(contract):
            raise RuntimeError("Invalid AFRIPower contract supplied")

        self._contract: ReadOnlyContract = contract

        self._receipts: Tuple[ReceiptSnapshot, ...] = tuple(
            self._normalize_receipt(r, contract)
            for r in receipts
        )

    def xǁReceiptProviderǁ__init____mutmut_2(
        self,
        receipts: Iterable[ReceiptSnapshot | Receipt] = (),
        contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
    ) -> None:

        if not assert_read_only_contract(None):
            raise RuntimeError("Invalid AFRIPower contract supplied")

        self._contract: ReadOnlyContract = contract

        self._receipts: Tuple[ReceiptSnapshot, ...] = tuple(
            self._normalize_receipt(r, contract)
            for r in receipts
        )

    def xǁReceiptProviderǁ__init____mutmut_3(
        self,
        receipts: Iterable[ReceiptSnapshot | Receipt] = (),
        contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
    ) -> None:

        if not assert_read_only_contract(contract):
            raise RuntimeError(None)

        self._contract: ReadOnlyContract = contract

        self._receipts: Tuple[ReceiptSnapshot, ...] = tuple(
            self._normalize_receipt(r, contract)
            for r in receipts
        )

    def xǁReceiptProviderǁ__init____mutmut_4(
        self,
        receipts: Iterable[ReceiptSnapshot | Receipt] = (),
        contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
    ) -> None:

        if not assert_read_only_contract(contract):
            raise RuntimeError("XXInvalid AFRIPower contract suppliedXX")

        self._contract: ReadOnlyContract = contract

        self._receipts: Tuple[ReceiptSnapshot, ...] = tuple(
            self._normalize_receipt(r, contract)
            for r in receipts
        )

    def xǁReceiptProviderǁ__init____mutmut_5(
        self,
        receipts: Iterable[ReceiptSnapshot | Receipt] = (),
        contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
    ) -> None:

        if not assert_read_only_contract(contract):
            raise RuntimeError("invalid afripower contract supplied")

        self._contract: ReadOnlyContract = contract

        self._receipts: Tuple[ReceiptSnapshot, ...] = tuple(
            self._normalize_receipt(r, contract)
            for r in receipts
        )

    def xǁReceiptProviderǁ__init____mutmut_6(
        self,
        receipts: Iterable[ReceiptSnapshot | Receipt] = (),
        contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
    ) -> None:

        if not assert_read_only_contract(contract):
            raise RuntimeError("INVALID AFRIPOWER CONTRACT SUPPLIED")

        self._contract: ReadOnlyContract = contract

        self._receipts: Tuple[ReceiptSnapshot, ...] = tuple(
            self._normalize_receipt(r, contract)
            for r in receipts
        )

    def xǁReceiptProviderǁ__init____mutmut_7(
        self,
        receipts: Iterable[ReceiptSnapshot | Receipt] = (),
        contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
    ) -> None:

        if not assert_read_only_contract(contract):
            raise RuntimeError("Invalid AFRIPower contract supplied")

        self._contract: ReadOnlyContract = None

        self._receipts: Tuple[ReceiptSnapshot, ...] = tuple(
            self._normalize_receipt(r, contract)
            for r in receipts
        )

    def xǁReceiptProviderǁ__init____mutmut_8(
        self,
        receipts: Iterable[ReceiptSnapshot | Receipt] = (),
        contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
    ) -> None:

        if not assert_read_only_contract(contract):
            raise RuntimeError("Invalid AFRIPower contract supplied")

        self._contract: ReadOnlyContract = contract

        self._receipts: Tuple[ReceiptSnapshot, ...] = None

    def xǁReceiptProviderǁ__init____mutmut_9(
        self,
        receipts: Iterable[ReceiptSnapshot | Receipt] = (),
        contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
    ) -> None:

        if not assert_read_only_contract(contract):
            raise RuntimeError("Invalid AFRIPower contract supplied")

        self._contract: ReadOnlyContract = contract

        self._receipts: Tuple[ReceiptSnapshot, ...] = tuple(
            None
        )

    def xǁReceiptProviderǁ__init____mutmut_10(
        self,
        receipts: Iterable[ReceiptSnapshot | Receipt] = (),
        contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
    ) -> None:

        if not assert_read_only_contract(contract):
            raise RuntimeError("Invalid AFRIPower contract supplied")

        self._contract: ReadOnlyContract = contract

        self._receipts: Tuple[ReceiptSnapshot, ...] = tuple(
            self._normalize_receipt(None, contract)
            for r in receipts
        )

    def xǁReceiptProviderǁ__init____mutmut_11(
        self,
        receipts: Iterable[ReceiptSnapshot | Receipt] = (),
        contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
    ) -> None:

        if not assert_read_only_contract(contract):
            raise RuntimeError("Invalid AFRIPower contract supplied")

        self._contract: ReadOnlyContract = contract

        self._receipts: Tuple[ReceiptSnapshot, ...] = tuple(
            self._normalize_receipt(r, None)
            for r in receipts
        )

    def xǁReceiptProviderǁ__init____mutmut_12(
        self,
        receipts: Iterable[ReceiptSnapshot | Receipt] = (),
        contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
    ) -> None:

        if not assert_read_only_contract(contract):
            raise RuntimeError("Invalid AFRIPower contract supplied")

        self._contract: ReadOnlyContract = contract

        self._receipts: Tuple[ReceiptSnapshot, ...] = tuple(
            self._normalize_receipt(contract)
            for r in receipts
        )

    def xǁReceiptProviderǁ__init____mutmut_13(
        self,
        receipts: Iterable[ReceiptSnapshot | Receipt] = (),
        contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
    ) -> None:

        if not assert_read_only_contract(contract):
            raise RuntimeError("Invalid AFRIPower contract supplied")

        self._contract: ReadOnlyContract = contract

        self._receipts: Tuple[ReceiptSnapshot, ...] = tuple(
            self._normalize_receipt(r, )
            for r in receipts
        )
    
    xǁReceiptProviderǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁReceiptProviderǁ__init____mutmut_1': xǁReceiptProviderǁ__init____mutmut_1, 
        'xǁReceiptProviderǁ__init____mutmut_2': xǁReceiptProviderǁ__init____mutmut_2, 
        'xǁReceiptProviderǁ__init____mutmut_3': xǁReceiptProviderǁ__init____mutmut_3, 
        'xǁReceiptProviderǁ__init____mutmut_4': xǁReceiptProviderǁ__init____mutmut_4, 
        'xǁReceiptProviderǁ__init____mutmut_5': xǁReceiptProviderǁ__init____mutmut_5, 
        'xǁReceiptProviderǁ__init____mutmut_6': xǁReceiptProviderǁ__init____mutmut_6, 
        'xǁReceiptProviderǁ__init____mutmut_7': xǁReceiptProviderǁ__init____mutmut_7, 
        'xǁReceiptProviderǁ__init____mutmut_8': xǁReceiptProviderǁ__init____mutmut_8, 
        'xǁReceiptProviderǁ__init____mutmut_9': xǁReceiptProviderǁ__init____mutmut_9, 
        'xǁReceiptProviderǁ__init____mutmut_10': xǁReceiptProviderǁ__init____mutmut_10, 
        'xǁReceiptProviderǁ__init____mutmut_11': xǁReceiptProviderǁ__init____mutmut_11, 
        'xǁReceiptProviderǁ__init____mutmut_12': xǁReceiptProviderǁ__init____mutmut_12, 
        'xǁReceiptProviderǁ__init____mutmut_13': xǁReceiptProviderǁ__init____mutmut_13
    }
    xǁReceiptProviderǁ__init____mutmut_orig.__name__ = 'xǁReceiptProviderǁ__init__'

    # -------------------------------------------------------------------------
    # INTERNAL NORMALIZATION
    # -------------------------------------------------------------------------

    @staticmethod
    def _normalize_receipt(
        receipt: ReceiptSnapshot | Receipt,
        contract: ReadOnlyContract,
    ) -> ReceiptSnapshot:

        if isinstance(receipt, ReceiptSnapshot):
            return receipt

        if not isinstance(receipt, Mapping):
            return ReceiptSnapshot(payload={}, contract=contract)

        return ReceiptSnapshot(
            payload=deepcopy(dict(receipt)),
            contract=contract,
        )

    # -------------------------------------------------------------------------
    # ACCESSORS
    # -------------------------------------------------------------------------

    @property
    def contract(self) -> ReadOnlyContract:
        """Return read-only contract."""
        return self._contract

    def list_receipts(self) -> Tuple[Dict[str, object], ...]:
        args = []# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁReceiptProviderǁlist_receipts__mutmut_orig'), object.__getattribute__(self, 'xǁReceiptProviderǁlist_receipts__mutmut_mutants'), args, kwargs, self)

    def xǁReceiptProviderǁlist_receipts__mutmut_orig(self) -> Tuple[Dict[str, object], ...]:
        """
        Return full enriched snapshots.

        ✅ Safe copies
        ✅ Metadata included
        """

        return tuple(r.canonical_dict() for r in self._receipts)

    def xǁReceiptProviderǁlist_receipts__mutmut_1(self) -> Tuple[Dict[str, object], ...]:
        """
        Return full enriched snapshots.

        ✅ Safe copies
        ✅ Metadata included
        """

        return tuple(None)
    
    xǁReceiptProviderǁlist_receipts__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁReceiptProviderǁlist_receipts__mutmut_1': xǁReceiptProviderǁlist_receipts__mutmut_1
    }
    xǁReceiptProviderǁlist_receipts__mutmut_orig.__name__ = 'xǁReceiptProviderǁlist_receipts'

    def raw_receipts(self) -> Tuple[Dict[str, object], ...]:
        args = []# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁReceiptProviderǁraw_receipts__mutmut_orig'), object.__getattribute__(self, 'xǁReceiptProviderǁraw_receipts__mutmut_mutants'), args, kwargs, self)

    def xǁReceiptProviderǁraw_receipts__mutmut_orig(self) -> Tuple[Dict[str, object], ...]:
        """
        Return only raw payloads (copied).

        ✅ No metadata
        ✅ Safe for metrics
        """

        return tuple(
            deepcopy(dict(r.payload)) for r in self._receipts
        )

    def xǁReceiptProviderǁraw_receipts__mutmut_1(self) -> Tuple[Dict[str, object], ...]:
        """
        Return only raw payloads (copied).

        ✅ No metadata
        ✅ Safe for metrics
        """

        return tuple(
            None
        )

    def xǁReceiptProviderǁraw_receipts__mutmut_2(self) -> Tuple[Dict[str, object], ...]:
        """
        Return only raw payloads (copied).

        ✅ No metadata
        ✅ Safe for metrics
        """

        return tuple(
            deepcopy(None) for r in self._receipts
        )

    def xǁReceiptProviderǁraw_receipts__mutmut_3(self) -> Tuple[Dict[str, object], ...]:
        """
        Return only raw payloads (copied).

        ✅ No metadata
        ✅ Safe for metrics
        """

        return tuple(
            copy(dict(r.payload)) for r in self._receipts
        )

    def xǁReceiptProviderǁraw_receipts__mutmut_4(self) -> Tuple[Dict[str, object], ...]:
        """
        Return only raw payloads (copied).

        ✅ No metadata
        ✅ Safe for metrics
        """

        return tuple(
            deepcopy(dict(None)) for r in self._receipts
        )
    
    xǁReceiptProviderǁraw_receipts__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁReceiptProviderǁraw_receipts__mutmut_1': xǁReceiptProviderǁraw_receipts__mutmut_1, 
        'xǁReceiptProviderǁraw_receipts__mutmut_2': xǁReceiptProviderǁraw_receipts__mutmut_2, 
        'xǁReceiptProviderǁraw_receipts__mutmut_3': xǁReceiptProviderǁraw_receipts__mutmut_3, 
        'xǁReceiptProviderǁraw_receipts__mutmut_4': xǁReceiptProviderǁraw_receipts__mutmut_4
    }
    xǁReceiptProviderǁraw_receipts__mutmut_orig.__name__ = 'xǁReceiptProviderǁraw_receipts'

    def count(self) -> int:
        """Return number of snapshots."""
        return len(self._receipts)

    def is_empty(self) -> bool:
        args = []# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁReceiptProviderǁis_empty__mutmut_orig'), object.__getattribute__(self, 'xǁReceiptProviderǁis_empty__mutmut_mutants'), args, kwargs, self)

    def xǁReceiptProviderǁis_empty__mutmut_orig(self) -> bool:
        """Check if provider is empty."""
        return len(self._receipts) == 0

    def xǁReceiptProviderǁis_empty__mutmut_1(self) -> bool:
        """Check if provider is empty."""
        return len(self._receipts) != 0

    def xǁReceiptProviderǁis_empty__mutmut_2(self) -> bool:
        """Check if provider is empty."""
        return len(self._receipts) == 1
    
    xǁReceiptProviderǁis_empty__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁReceiptProviderǁis_empty__mutmut_1': xǁReceiptProviderǁis_empty__mutmut_1, 
        'xǁReceiptProviderǁis_empty__mutmut_2': xǁReceiptProviderǁis_empty__mutmut_2
    }
    xǁReceiptProviderǁis_empty__mutmut_orig.__name__ = 'xǁReceiptProviderǁis_empty'

    def iter_receipts(self) -> Iterable[Dict[str, object]]:
        """
        Lazy iterator (safe copies).
        """

        for r in self._receipts:
            yield r.canonical_dict()

    # -------------------------------------------------------------------------
    # FILTER HELPERS (PURE)
    # -------------------------------------------------------------------------

    def filter_by_execution_id(self, execution_id: str) -> List[Dict[str, object]]:
        args = [execution_id]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁReceiptProviderǁfilter_by_execution_id__mutmut_orig'), object.__getattribute__(self, 'xǁReceiptProviderǁfilter_by_execution_id__mutmut_mutants'), args, kwargs, self)

    # -------------------------------------------------------------------------
    # FILTER HELPERS (PURE)
    # -------------------------------------------------------------------------

    def xǁReceiptProviderǁfilter_by_execution_id__mutmut_orig(self, execution_id: str) -> List[Dict[str, object]]:
        """
        Pure filter helper.

        ✅ No mutation
        ✅ No authority
        """

        results: List[Dict[str, object]] = []

        for r in self._receipts:
            rid = r.payload.get("execution_id")
            if rid == execution_id:
                results.append(deepcopy(dict(r.payload)))

        return results

    # -------------------------------------------------------------------------
    # FILTER HELPERS (PURE)
    # -------------------------------------------------------------------------

    def xǁReceiptProviderǁfilter_by_execution_id__mutmut_1(self, execution_id: str) -> List[Dict[str, object]]:
        """
        Pure filter helper.

        ✅ No mutation
        ✅ No authority
        """

        results: List[Dict[str, object]] = None

        for r in self._receipts:
            rid = r.payload.get("execution_id")
            if rid == execution_id:
                results.append(deepcopy(dict(r.payload)))

        return results

    # -------------------------------------------------------------------------
    # FILTER HELPERS (PURE)
    # -------------------------------------------------------------------------

    def xǁReceiptProviderǁfilter_by_execution_id__mutmut_2(self, execution_id: str) -> List[Dict[str, object]]:
        """
        Pure filter helper.

        ✅ No mutation
        ✅ No authority
        """

        results: List[Dict[str, object]] = []

        for r in self._receipts:
            rid = None
            if rid == execution_id:
                results.append(deepcopy(dict(r.payload)))

        return results

    # -------------------------------------------------------------------------
    # FILTER HELPERS (PURE)
    # -------------------------------------------------------------------------

    def xǁReceiptProviderǁfilter_by_execution_id__mutmut_3(self, execution_id: str) -> List[Dict[str, object]]:
        """
        Pure filter helper.

        ✅ No mutation
        ✅ No authority
        """

        results: List[Dict[str, object]] = []

        for r in self._receipts:
            rid = r.payload.get(None)
            if rid == execution_id:
                results.append(deepcopy(dict(r.payload)))

        return results

    # -------------------------------------------------------------------------
    # FILTER HELPERS (PURE)
    # -------------------------------------------------------------------------

    def xǁReceiptProviderǁfilter_by_execution_id__mutmut_4(self, execution_id: str) -> List[Dict[str, object]]:
        """
        Pure filter helper.

        ✅ No mutation
        ✅ No authority
        """

        results: List[Dict[str, object]] = []

        for r in self._receipts:
            rid = r.payload.get("XXexecution_idXX")
            if rid == execution_id:
                results.append(deepcopy(dict(r.payload)))

        return results

    # -------------------------------------------------------------------------
    # FILTER HELPERS (PURE)
    # -------------------------------------------------------------------------

    def xǁReceiptProviderǁfilter_by_execution_id__mutmut_5(self, execution_id: str) -> List[Dict[str, object]]:
        """
        Pure filter helper.

        ✅ No mutation
        ✅ No authority
        """

        results: List[Dict[str, object]] = []

        for r in self._receipts:
            rid = r.payload.get("EXECUTION_ID")
            if rid == execution_id:
                results.append(deepcopy(dict(r.payload)))

        return results

    # -------------------------------------------------------------------------
    # FILTER HELPERS (PURE)
    # -------------------------------------------------------------------------

    def xǁReceiptProviderǁfilter_by_execution_id__mutmut_6(self, execution_id: str) -> List[Dict[str, object]]:
        """
        Pure filter helper.

        ✅ No mutation
        ✅ No authority
        """

        results: List[Dict[str, object]] = []

        for r in self._receipts:
            rid = r.payload.get("execution_id")
            if rid != execution_id:
                results.append(deepcopy(dict(r.payload)))

        return results

    # -------------------------------------------------------------------------
    # FILTER HELPERS (PURE)
    # -------------------------------------------------------------------------

    def xǁReceiptProviderǁfilter_by_execution_id__mutmut_7(self, execution_id: str) -> List[Dict[str, object]]:
        """
        Pure filter helper.

        ✅ No mutation
        ✅ No authority
        """

        results: List[Dict[str, object]] = []

        for r in self._receipts:
            rid = r.payload.get("execution_id")
            if rid == execution_id:
                results.append(None)

        return results

    # -------------------------------------------------------------------------
    # FILTER HELPERS (PURE)
    # -------------------------------------------------------------------------

    def xǁReceiptProviderǁfilter_by_execution_id__mutmut_8(self, execution_id: str) -> List[Dict[str, object]]:
        """
        Pure filter helper.

        ✅ No mutation
        ✅ No authority
        """

        results: List[Dict[str, object]] = []

        for r in self._receipts:
            rid = r.payload.get("execution_id")
            if rid == execution_id:
                results.append(deepcopy(None))

        return results

    # -------------------------------------------------------------------------
    # FILTER HELPERS (PURE)
    # -------------------------------------------------------------------------

    def xǁReceiptProviderǁfilter_by_execution_id__mutmut_9(self, execution_id: str) -> List[Dict[str, object]]:
        """
        Pure filter helper.

        ✅ No mutation
        ✅ No authority
        """

        results: List[Dict[str, object]] = []

        for r in self._receipts:
            rid = r.payload.get("execution_id")
            if rid == execution_id:
                results.append(copy(dict(r.payload)))

        return results

    # -------------------------------------------------------------------------
    # FILTER HELPERS (PURE)
    # -------------------------------------------------------------------------

    def xǁReceiptProviderǁfilter_by_execution_id__mutmut_10(self, execution_id: str) -> List[Dict[str, object]]:
        """
        Pure filter helper.

        ✅ No mutation
        ✅ No authority
        """

        results: List[Dict[str, object]] = []

        for r in self._receipts:
            rid = r.payload.get("execution_id")
            if rid == execution_id:
                results.append(deepcopy(dict(None)))

        return results
    
    xǁReceiptProviderǁfilter_by_execution_id__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁReceiptProviderǁfilter_by_execution_id__mutmut_1': xǁReceiptProviderǁfilter_by_execution_id__mutmut_1, 
        'xǁReceiptProviderǁfilter_by_execution_id__mutmut_2': xǁReceiptProviderǁfilter_by_execution_id__mutmut_2, 
        'xǁReceiptProviderǁfilter_by_execution_id__mutmut_3': xǁReceiptProviderǁfilter_by_execution_id__mutmut_3, 
        'xǁReceiptProviderǁfilter_by_execution_id__mutmut_4': xǁReceiptProviderǁfilter_by_execution_id__mutmut_4, 
        'xǁReceiptProviderǁfilter_by_execution_id__mutmut_5': xǁReceiptProviderǁfilter_by_execution_id__mutmut_5, 
        'xǁReceiptProviderǁfilter_by_execution_id__mutmut_6': xǁReceiptProviderǁfilter_by_execution_id__mutmut_6, 
        'xǁReceiptProviderǁfilter_by_execution_id__mutmut_7': xǁReceiptProviderǁfilter_by_execution_id__mutmut_7, 
        'xǁReceiptProviderǁfilter_by_execution_id__mutmut_8': xǁReceiptProviderǁfilter_by_execution_id__mutmut_8, 
        'xǁReceiptProviderǁfilter_by_execution_id__mutmut_9': xǁReceiptProviderǁfilter_by_execution_id__mutmut_9, 
        'xǁReceiptProviderǁfilter_by_execution_id__mutmut_10': xǁReceiptProviderǁfilter_by_execution_id__mutmut_10
    }
    xǁReceiptProviderǁfilter_by_execution_id__mutmut_orig.__name__ = 'xǁReceiptProviderǁfilter_by_execution_id'


# =============================================================================
# BUILDERS
# =============================================================================


def build_receipt_provider(
    receipts: Iterable[ReceiptSnapshot | Receipt],
    contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
) -> ReceiptProvider:
    args = [receipts, contract]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_receipt_provider__mutmut_orig, x_build_receipt_provider__mutmut_mutants, args, kwargs, None)


# =============================================================================
# BUILDERS
# =============================================================================


def x_build_receipt_provider__mutmut_orig(
    receipts: Iterable[ReceiptSnapshot | Receipt],
    contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
) -> ReceiptProvider:
    """Factory for provider."""
    return ReceiptProvider(receipts=receipts, contract=contract)


# =============================================================================
# BUILDERS
# =============================================================================


def x_build_receipt_provider__mutmut_1(
    receipts: Iterable[ReceiptSnapshot | Receipt],
    contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
) -> ReceiptProvider:
    """Factory for provider."""
    return ReceiptProvider(receipts=None, contract=contract)


# =============================================================================
# BUILDERS
# =============================================================================


def x_build_receipt_provider__mutmut_2(
    receipts: Iterable[ReceiptSnapshot | Receipt],
    contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
) -> ReceiptProvider:
    """Factory for provider."""
    return ReceiptProvider(receipts=receipts, contract=None)


# =============================================================================
# BUILDERS
# =============================================================================


def x_build_receipt_provider__mutmut_3(
    receipts: Iterable[ReceiptSnapshot | Receipt],
    contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
) -> ReceiptProvider:
    """Factory for provider."""
    return ReceiptProvider(contract=contract)


# =============================================================================
# BUILDERS
# =============================================================================


def x_build_receipt_provider__mutmut_4(
    receipts: Iterable[ReceiptSnapshot | Receipt],
    contract: ReadOnlyContract = DEFAULT_READ_ONLY_CONTRACT,
) -> ReceiptProvider:
    """Factory for provider."""
    return ReceiptProvider(receipts=receipts, )

x_build_receipt_provider__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_receipt_provider__mutmut_1': x_build_receipt_provider__mutmut_1, 
    'x_build_receipt_provider__mutmut_2': x_build_receipt_provider__mutmut_2, 
    'x_build_receipt_provider__mutmut_3': x_build_receipt_provider__mutmut_3, 
    'x_build_receipt_provider__mutmut_4': x_build_receipt_provider__mutmut_4
}
x_build_receipt_provider__mutmut_orig.__name__ = 'x_build_receipt_provider'


def empty_receipt_provider() -> ReceiptProvider:
    args = []# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_empty_receipt_provider__mutmut_orig, x_empty_receipt_provider__mutmut_mutants, args, kwargs, None)


def x_empty_receipt_provider__mutmut_orig() -> ReceiptProvider:
    """Empty provider."""
    return ReceiptProvider(receipts=())


def x_empty_receipt_provider__mutmut_1() -> ReceiptProvider:
    """Empty provider."""
    return ReceiptProvider(receipts=None)

x_empty_receipt_provider__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_empty_receipt_provider__mutmut_1': x_empty_receipt_provider__mutmut_1
}
x_empty_receipt_provider__mutmut_orig.__name__ = 'x_empty_receipt_provider'


# =============================================================================
# METADATA
# =============================================================================


def receipt_provider_metadata() -> Dict[str, object]:
    args = []# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_receipt_provider_metadata__mutmut_orig, x_receipt_provider_metadata__mutmut_mutants, args, kwargs, None)


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_orig() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_1() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "XXprovider_statusXX": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_2() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "PROVIDER_STATUS": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_3() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "XXruntime_authorityXX": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_4() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "RUNTIME_AUTHORITY": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_5() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "XXenforcement_authorityXX": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_6() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "ENFORCEMENT_AUTHORITY": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_7() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "XXvalidation_authorityXX": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_8() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "VALIDATION_AUTHORITY": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_9() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "XXgovernance_authorityXX": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_10() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "GOVERNANCE_AUTHORITY": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_11() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "XXintelligence_authorityXX": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_12() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "INTELLIGENCE_AUTHORITY": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_13() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "XXexecution_authorityXX": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_14() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "EXECUTION_AUTHORITY": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_15() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "XXreplay_authorityXX": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_16() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "REPLAY_AUTHORITY": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_17() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "XXproof_authorityXX": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_18() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "PROOF_AUTHORITY": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_19() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "XXread_onlyXX": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_20() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "READ_ONLY": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_21() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "XXdisplay_onlyXX": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_22() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "DISPLAY_ONLY": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_23() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "XXobservational_onlyXX": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_24() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "OBSERVATIONAL_ONLY": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_25() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "XXauthoritativeXX": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_26() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "AUTHORITATIVE": AUTHORITATIVE,

        # Contract binding
        "contract_valid": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_27() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "XXcontract_validXX": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_28() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "CONTRACT_VALID": True,
    }


# =============================================================================
# METADATA
# =============================================================================


def x_receipt_provider_metadata__mutmut_29() -> Dict[str, object]:
    """Canonical metadata for CI / checkpoints."""

    return {
        "provider_status": PROVIDER_STATUS,

        # Authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,

        # Behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "authoritative": AUTHORITATIVE,

        # Contract binding
        "contract_valid": False,
    }

x_receipt_provider_metadata__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_receipt_provider_metadata__mutmut_1': x_receipt_provider_metadata__mutmut_1, 
    'x_receipt_provider_metadata__mutmut_2': x_receipt_provider_metadata__mutmut_2, 
    'x_receipt_provider_metadata__mutmut_3': x_receipt_provider_metadata__mutmut_3, 
    'x_receipt_provider_metadata__mutmut_4': x_receipt_provider_metadata__mutmut_4, 
    'x_receipt_provider_metadata__mutmut_5': x_receipt_provider_metadata__mutmut_5, 
    'x_receipt_provider_metadata__mutmut_6': x_receipt_provider_metadata__mutmut_6, 
    'x_receipt_provider_metadata__mutmut_7': x_receipt_provider_metadata__mutmut_7, 
    'x_receipt_provider_metadata__mutmut_8': x_receipt_provider_metadata__mutmut_8, 
    'x_receipt_provider_metadata__mutmut_9': x_receipt_provider_metadata__mutmut_9, 
    'x_receipt_provider_metadata__mutmut_10': x_receipt_provider_metadata__mutmut_10, 
    'x_receipt_provider_metadata__mutmut_11': x_receipt_provider_metadata__mutmut_11, 
    'x_receipt_provider_metadata__mutmut_12': x_receipt_provider_metadata__mutmut_12, 
    'x_receipt_provider_metadata__mutmut_13': x_receipt_provider_metadata__mutmut_13, 
    'x_receipt_provider_metadata__mutmut_14': x_receipt_provider_metadata__mutmut_14, 
    'x_receipt_provider_metadata__mutmut_15': x_receipt_provider_metadata__mutmut_15, 
    'x_receipt_provider_metadata__mutmut_16': x_receipt_provider_metadata__mutmut_16, 
    'x_receipt_provider_metadata__mutmut_17': x_receipt_provider_metadata__mutmut_17, 
    'x_receipt_provider_metadata__mutmut_18': x_receipt_provider_metadata__mutmut_18, 
    'x_receipt_provider_metadata__mutmut_19': x_receipt_provider_metadata__mutmut_19, 
    'x_receipt_provider_metadata__mutmut_20': x_receipt_provider_metadata__mutmut_20, 
    'x_receipt_provider_metadata__mutmut_21': x_receipt_provider_metadata__mutmut_21, 
    'x_receipt_provider_metadata__mutmut_22': x_receipt_provider_metadata__mutmut_22, 
    'x_receipt_provider_metadata__mutmut_23': x_receipt_provider_metadata__mutmut_23, 
    'x_receipt_provider_metadata__mutmut_24': x_receipt_provider_metadata__mutmut_24, 
    'x_receipt_provider_metadata__mutmut_25': x_receipt_provider_metadata__mutmut_25, 
    'x_receipt_provider_metadata__mutmut_26': x_receipt_provider_metadata__mutmut_26, 
    'x_receipt_provider_metadata__mutmut_27': x_receipt_provider_metadata__mutmut_27, 
    'x_receipt_provider_metadata__mutmut_28': x_receipt_provider_metadata__mutmut_28, 
    'x_receipt_provider_metadata__mutmut_29': x_receipt_provider_metadata__mutmut_29
}
x_receipt_provider_metadata__mutmut_orig.__name__ = 'x_receipt_provider_metadata'


# =============================================================================
# VALIDATION HELPER (CI USE)
# =============================================================================


def assert_provider_integrity(provider: ReceiptProvider) -> bool:
    args = [provider]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_assert_provider_integrity__mutmut_orig, x_assert_provider_integrity__mutmut_mutants, args, kwargs, None)


# =============================================================================
# VALIDATION HELPER (CI USE)
# =============================================================================


def x_assert_provider_integrity__mutmut_orig(provider: ReceiptProvider) -> bool:
    """
    Ensure provider remains non-authoritative.

    ✅ Structural check only
    """

    return (
        provider.AUTHORITY is False
        and assert_read_only_contract(provider.contract)
    )


# =============================================================================
# VALIDATION HELPER (CI USE)
# =============================================================================


def x_assert_provider_integrity__mutmut_1(provider: ReceiptProvider) -> bool:
    """
    Ensure provider remains non-authoritative.

    ✅ Structural check only
    """

    return (
        provider.AUTHORITY is False or assert_read_only_contract(provider.contract)
    )


# =============================================================================
# VALIDATION HELPER (CI USE)
# =============================================================================


def x_assert_provider_integrity__mutmut_2(provider: ReceiptProvider) -> bool:
    """
    Ensure provider remains non-authoritative.

    ✅ Structural check only
    """

    return (
        provider.AUTHORITY is not False
        and assert_read_only_contract(provider.contract)
    )


# =============================================================================
# VALIDATION HELPER (CI USE)
# =============================================================================


def x_assert_provider_integrity__mutmut_3(provider: ReceiptProvider) -> bool:
    """
    Ensure provider remains non-authoritative.

    ✅ Structural check only
    """

    return (
        provider.AUTHORITY is True
        and assert_read_only_contract(provider.contract)
    )


# =============================================================================
# VALIDATION HELPER (CI USE)
# =============================================================================


def x_assert_provider_integrity__mutmut_4(provider: ReceiptProvider) -> bool:
    """
    Ensure provider remains non-authoritative.

    ✅ Structural check only
    """

    return (
        provider.AUTHORITY is False
        and assert_read_only_contract(None)
    )

x_assert_provider_integrity__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_assert_provider_integrity__mutmut_1': x_assert_provider_integrity__mutmut_1, 
    'x_assert_provider_integrity__mutmut_2': x_assert_provider_integrity__mutmut_2, 
    'x_assert_provider_integrity__mutmut_3': x_assert_provider_integrity__mutmut_3, 
    'x_assert_provider_integrity__mutmut_4': x_assert_provider_integrity__mutmut_4
}
x_assert_provider_integrity__mutmut_orig.__name__ = 'x_assert_provider_integrity'


# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    "ReceiptSnapshot",
    "ReceiptProvider",
    "build_receipt_provider",
    "empty_receipt_provider",
    "receipt_provider_metadata",
    "assert_provider_integrity",
]