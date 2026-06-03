"""
Read-only governance impact index.

The Impact Index answers reference questions such as:

    "Which executions reference this governance object?"

Constitutional Law
------------------
Impact index is read-only.
Impact index is reference-only.
Impact index does not govern.
Impact index does not validate.
Impact index does not execute.
Impact index does not mutate receipts.
Impact index does not create runtime, replay, proof, CI, or governance authority.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

IMPACT_INDEX_STATUS = "READ_ONLY_IMPACT_INDEX"

REFERENCE_ONLY = True
READ_ONLY = True
DISPLAY_ONLY = True

RUNTIME_AUTHORITY = False
ENFORCEMENT_AUTHORITY = False
VALIDATION_AUTHORITY = False
REPLAY_AUTHORITY = False
PROOF_AUTHORITY = False
CI_AUTHORITY = False
GOVERNANCE_AUTHORITY = False

RUNTIME_DEPENDENCY = False
PROJECTION_DEPENDENCY = False
MUTATION_ALLOWED = False
RECEIPT_MUTATION_ALLOWED = False

TRACEABILITY_FIELD = "governance_traceability"


@dataclass(frozen=True)
class ImpactRecord:
    """Immutable reference-only impact record."""

    governance_id: str
    execution_id: str
    reference_type: str = ""

    def canonical_dict(self) -> dict[str, object]:
        return {
            "governance_id": self.governance_id,
            "execution_id": self.execution_id,
            "reference_type": self.reference_type,
            "impact_index_status": IMPACT_INDEX_STATUS,
            "reference_only": REFERENCE_ONLY,
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "runtime_authority": RUNTIME_AUTHORITY,
            "validation_authority": VALIDATION_AUTHORITY,
            "governance_authority": GOVERNANCE_AUTHORITY,
        }


@dataclass(frozen=True)
class ImpactIndex:
    """Immutable read-only index of governance references."""

    records: tuple[ImpactRecord, ...]

    def impacted_executions(self, governance_id: str) -> tuple[str, ...]:
        """Return execution IDs that reference the governance ID."""

        target = _safe_str(governance_id)

        return tuple(
            record.execution_id
            for record in self.records
            if record.governance_id == target
        )

    def records_for_governance(
        self,
        governance_id: str,
    ) -> tuple[ImpactRecord, ...]:
        """Return impact records for a governance ID."""

        target = _safe_str(governance_id)

        return tuple(
            record
            for record in self.records
            if record.governance_id == target
        )

    def canonical_dict_for_governance(
        self,
        governance_id: str,
    ) -> dict[str, object]:
        """Return display-only impact payload for one governance ID."""

        records = self.records_for_governance(governance_id)

        return {
            "governance_id": _safe_str(governance_id),
            "impact_index_status": IMPACT_INDEX_STATUS,
            "reference_only": REFERENCE_ONLY,
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "runtime_authority": RUNTIME_AUTHORITY,
            "validation_authority": VALIDATION_AUTHORITY,
            "governance_authority": GOVERNANCE_AUTHORITY,
            "impacted_executions": [
                record.execution_id for record in records
            ],
            "records": [record.canonical_dict() for record in records],
        }


def _safe_str(value: object) -> str:
    """Return deterministic stripped string or empty string."""

    if isinstance(value, str):
        return value.strip()

    return ""


def _extract_execution_id(receipt: Mapping[str, object]) -> str:
    """Extract execution ID from a receipt-like object."""

    return _safe_str(receipt.get("execution_id"))


def _extract_references(
    receipt: Mapping[str, object],
) -> tuple[dict[str, str], ...]:
    """Extract reference-only governance traceability entries."""

    raw_refs = receipt.get(TRACEABILITY_FIELD, [])

    if not isinstance(raw_refs, Sequence) or isinstance(
        raw_refs,
        (str, bytes),
    ):
        return ()

    references: list[dict[str, str]] = []

    for raw_ref in raw_refs:
        if not isinstance(raw_ref, Mapping):
            continue

        ref_id = _safe_str(raw_ref.get("id"))
        ref_type = _safe_str(raw_ref.get("type"))

        if not ref_id:
            continue

        references.append(
            {
                "id": ref_id,
                "type": ref_type,
            }
        )

    return tuple(references)


def build_impact_index(
    receipts: Iterable[Mapping[str, object]],
) -> ImpactIndex:
    """Build immutable read-only impact index from receipt-like payloads."""

    records: list[ImpactRecord] = []

    for receipt in receipts:
        execution_id = _extract_execution_id(receipt)

        if not execution_id:
            continue

        for reference in _extract_references(receipt):
            records.append(
                ImpactRecord(
                    governance_id=reference["id"],
                    execution_id=execution_id,
                    reference_type=reference["type"],
                )
            )

    return ImpactIndex(records=tuple(records))


def impacted_executions_for_governance(
    governance_id: str,
    receipts: Iterable[Mapping[str, object]],
) -> tuple[str, ...]:
    """Convenience helper returning impacted execution IDs."""

    return build_impact_index(receipts).impacted_executions(governance_id)


def impact_payload_for_governance(
    governance_id: str,
    receipts: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    """Return display-only governance impact payload."""

    return build_impact_index(receipts).canonical_dict_for_governance(
        governance_id,
    )