"""
Read-only governance impact query helpers.

The impact query layer answers display/reference questions such as:

    "Which executions reference ADR-0016?"
    "Which receipts reference RULE-016-4?"

Constitutional Law
------------------
Impact query is read-only.
Impact query is reference-only.
Impact query does not govern.
Impact query does not validate.
Impact query does not execute.
Impact query does not mutate receipts.
Impact query does not create runtime, replay, proof, CI, or governance authority.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from afritech.impact.impact_index import (
    CI_AUTHORITY,
    DISPLAY_ONLY,
    ENFORCEMENT_AUTHORITY,
    GOVERNANCE_AUTHORITY,
    IMPACT_INDEX_STATUS,
    PROOF_AUTHORITY,
    READ_ONLY,
    REFERENCE_ONLY,
    REPLAY_AUTHORITY,
    RUNTIME_AUTHORITY,
    VALIDATION_AUTHORITY,
    ImpactIndex,
    ImpactRecord,
    build_impact_index,
)


IMPACT_QUERY_STATUS = "READ_ONLY_IMPACT_QUERY"

QUERY_AUTHORITY = False
DECISION_AUTHORITY = False
ADMISSIBILITY_AUTHORITY = False
MUTATION_ALLOWED = False


def query_impacted_executions(
    governance_id: str,
    receipts: Iterable[Mapping[str, object]],
) -> tuple[str, ...]:
    """Return execution IDs that reference a governance ID.

    This function performs reference lookup only.
    It does not validate governance truth or runtime correctness.
    """

    return build_impact_index(receipts).impacted_executions(governance_id)


def query_impact_records(
    governance_id: str,
    receipts: Iterable[Mapping[str, object]],
) -> tuple[ImpactRecord, ...]:
    """Return reference-only impact records for a governance ID."""

    return build_impact_index(receipts).records_for_governance(governance_id)


def query_impact_payload(
    governance_id: str,
    receipts: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    """Return display-only impact payload for a governance ID.

    This function deliberately avoids dict.update(...) so validator
    rules can reject mutation-style APIs consistently.
    """

    index = build_impact_index(receipts)
    payload = index.canonical_dict_for_governance(governance_id)

    return {
        **payload,
        "impact_query_status": IMPACT_QUERY_STATUS,
        "impact_index_status": IMPACT_INDEX_STATUS,
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "query_authority": QUERY_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "mutation_allowed": MUTATION_ALLOWED,
    }


def query_all_impacts(
    receipts: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    """Return display-only impact payload for all governance references."""

    index: ImpactIndex = build_impact_index(receipts)

    grouped: dict[str, list[dict[str, object]]] = {}

    for record in index.records:
        if record.governance_id not in grouped:
            grouped[record.governance_id] = []

        grouped[record.governance_id].append(record.canonical_dict())

    return {
        "impact_query_status": IMPACT_QUERY_STATUS,
        "impact_index_status": IMPACT_INDEX_STATUS,
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "query_authority": QUERY_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "mutation_allowed": MUTATION_ALLOWED,
        "impacts": grouped,
    }


def has_impact_reference(
    governance_id: str,
    receipts: Iterable[Mapping[str, object]],
) -> bool:
    """Return whether a governance ID is referenced.

    This is reference presence only, not governance validation.
    """

    return bool(query_impacted_executions(governance_id, receipts))