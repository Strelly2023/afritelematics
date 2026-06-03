"""Attach reference-only governance traceability metadata to receipt copies."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .references import GovernanceReference, TraceabilityBundle


BRIDGE_STATUS = "REFERENCE_ONLY"
REFERENCE_ONLY = True
RUNTIME_AUTHORITY = False
ENFORCEMENT_AUTHORITY = False
PROJECTION_DEPENDENCY = False
TRACEABILITY_FIELD = "governance_traceability"


def attach_traceability(
    receipt: Mapping[str, Any],
    refs: Iterable[GovernanceReference],
) -> dict[str, Any]:
    """Return a receipt copy enriched with governance reference identifiers."""

    bundle = TraceabilityBundle.from_references(tuple(refs))
    enriched = dict(receipt)
    enriched[TRACEABILITY_FIELD] = bundle.as_list()
    enriched["traceability_bridge"] = {
        "status": BRIDGE_STATUS,
        "reference_only": REFERENCE_ONLY,
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "projection_dependency": PROJECTION_DEPENDENCY,
    }
    return enriched
