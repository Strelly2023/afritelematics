"""
Read-only in-memory explanation store.

This module exists only to support explanatory and dashboard surfaces.

It MUST NEVER:
- decide runtime behavior
- validate truth
- enforce governance
- mutate proof authority
- become a source of constitutional authority
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Tuple, Dict, List
#afritech/explainability/store.py
# =============================================================================
# CONSTANTS (STRICT NON-AUTHORITY)
# =============================================================================

STORE_STATUS = "READ_ONLY_EXPLANATION_STORE"
STORE_VERSION = "1.0"

RUNTIME_AUTHORITY: bool = False
ENFORCEMENT_AUTHORITY: bool = False
VALIDATION_AUTHORITY: bool = False
GOVERNANCE_AUTHORITY: bool = False
REPLAY_AUTHORITY: bool = False
PROOF_AUTHORITY: bool = False
INTELLIGENCE_AUTHORITY: bool = False

READ_ONLY: bool = True
DISPLAY_ONLY: bool = True

AUTHORITATIVE: bool = False

# =============================================================================
# RECORD MODEL
# =============================================================================


@dataclass(frozen=True)
class ExecutionExplanationRecord:
    """
    Immutable explanation record.

    ✅ Deep-copied
    ✅ Observational only
    ✅ Non-authoritative
    """

    execution_id: str
    receipt: Mapping[str, Any] = field(default_factory=dict)
    explanation: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Defensive deep copy to prevent external mutation
        object.__setattr__(self, "receipt", deepcopy(dict(self.receipt)))
        object.__setattr__(self, "explanation", deepcopy(dict(self.explanation)))

    def canonical_dict(self) -> Dict[str, object]:
        """Return safe, copied record with metadata."""

        return {
            "execution_id": self.execution_id,
            "receipt": deepcopy(dict(self.receipt)),
            "explanation": deepcopy(dict(self.explanation)),

            # metadata
            "store_status": STORE_STATUS,

            # authority flags (ALL FALSE)
            "runtime_authority": RUNTIME_AUTHORITY,
            "enforcement_authority": ENFORCEMENT_AUTHORITY,
            "validation_authority": VALIDATION_AUTHORITY,
            "governance_authority": GOVERNANCE_AUTHORITY,
            "replay_authority": REPLAY_AUTHORITY,
            "proof_authority": PROOF_AUTHORITY,
            "intelligence_authority": INTELLIGENCE_AUTHORITY,

            # behavior flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "authoritative": AUTHORITATIVE,
        }


# =============================================================================
# STORE
# =============================================================================


class ExecutionExplanationStore:
    """
    Read-only explanation store.

    ✅ No mutation APIs
    ✅ No runtime linkage
    ✅ No persistence
    ✅ Deterministic
    """

    AUTHORITY = False

    def __init__(
        self,
        records: Iterable[ExecutionExplanationRecord | Mapping[str, Any]] = (),
    ) -> None:
        self._records: Tuple[ExecutionExplanationRecord, ...] = tuple(
            self._normalize_record(r) for r in records
        )

    # -------------------------------------------------------------------------
    # NORMALIZATION
    # -------------------------------------------------------------------------

    @staticmethod
    def _normalize_record(
        record: ExecutionExplanationRecord | Mapping[str, Any],
    ) -> ExecutionExplanationRecord:

        if isinstance(record, ExecutionExplanationRecord):
            return record

        if not isinstance(record, Mapping):
            return ExecutionExplanationRecord(
                execution_id="",
                receipt={},
                explanation={},
            )

        execution_id = record.get("execution_id")
        if not isinstance(execution_id, str):
            execution_id = ""

        receipt = record.get("receipt", record)
        if not isinstance(receipt, Mapping):
            receipt = {}

        explanation = record.get("explanation", {})
        if not isinstance(explanation, Mapping):
            explanation = {}

        return ExecutionExplanationRecord(
            execution_id=execution_id,
            receipt=dict(receipt),
            explanation=dict(explanation),
        )

    # -------------------------------------------------------------------------
    # ACCESSORS (PURE)
    # -------------------------------------------------------------------------

    def all(self) -> Tuple[Dict[str, object], ...]:
        """Return all records (safe copies)."""

        return tuple(r.canonical_dict() for r in self._records)

    def receipts(self) -> Tuple[Dict[str, object], ...]:
        """Return raw receipt payloads only (safe copies)."""

        return tuple(
            deepcopy(dict(r.receipt)) for r in self._records
        )

    def explanations(self) -> Tuple[Dict[str, object], ...]:
        """Return explanation payloads only."""

        return tuple(
            deepcopy(dict(r.explanation)) for r in self._records
        )

    def get(self, execution_id: str) -> Dict[str, object] | None:
        """Get one record by execution ID."""

        for r in self._records:
            if r.execution_id == execution_id:
                return r.canonical_dict()
        return None

    def get_receipt(self, execution_id: str) -> Dict[str, object] | None:
        """Get one receipt by execution ID."""

        for r in self._records:
            if r.execution_id == execution_id:
                return deepcopy(dict(r.receipt))
        return None

    def get_explanation(self, execution_id: str) -> Dict[str, object] | None:
        """Get one explanation by execution ID."""

        for r in self._records:
            if r.execution_id == execution_id:
                return deepcopy(dict(r.explanation))
        return None

    def exists(self, execution_id: str) -> bool:
        """Check existence of a record."""

        return any(r.execution_id == execution_id for r in self._records)

    def count(self) -> int:
        """Number of records."""

        return len(self._records)

    def is_empty(self) -> bool:
        """Check if store is empty."""

        return len(self._records) == 0

    # -------------------------------------------------------------------------
    # FILTER HELPERS
    # -------------------------------------------------------------------------

    def filter_by_execution_prefix(self, prefix: str) -> List[Dict[str, object]]:
        """
        Filter records by execution_id prefix.

        ✅ Pure
        ✅ Non-authoritative
        """

        if not isinstance(prefix, str) or not prefix:
            return []

        results: List[Dict[str, object]] = []

        for r in self._records:
            if r.execution_id.startswith(prefix):
                results.append(r.canonical_dict())

        return results


# =============================================================================
# BUILDERS
# =============================================================================


def build_store(
    records: Iterable[ExecutionExplanationRecord | Mapping[str, Any]],
) -> ExecutionExplanationStore:
    """Factory for read-only store."""

    return ExecutionExplanationStore(records)


def empty_store() -> ExecutionExplanationStore:
    """Empty explanation store."""

    return ExecutionExplanationStore(records=())


# =============================================================================
# METADATA
# =============================================================================


def store_metadata() -> Dict[str, object]:
    """
    Canonical store metadata for validators / CI.

    ✅ Pure
    ✅ Deterministic
    """

    return {
        "store_status": STORE_STATUS,
        "version": STORE_VERSION,

        # authority flags
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,

        # behavior flags
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "authoritative": AUTHORITATIVE,
    }


# =============================================================================
# VALIDATION HELPER (CI USE)
# =============================================================================


def assert_store_integrity(store: ExecutionExplanationStore) -> bool:
    """
    Structural integrity check.

    ✅ Ensures non-authoritative behavior
    """

    return (
        store.AUTHORITY is False
        and READ_ONLY is True
        and DISPLAY_ONLY is True
    )


# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    "ExecutionExplanationRecord",
    "ExecutionExplanationStore",
    "build_store",
    "empty_store",
    "store_metadata",
    "assert_store_integrity",
]