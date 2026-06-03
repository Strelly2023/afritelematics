"""
AFRIPower dashboard constants.

The dashboard is a read-only visualization surface.

It may display:
- graph summaries
- projection metrics
- receipt/reference counts
- insight summaries

It must not:
- execute runtime behavior
- validate truth
- create authority
- mutate artifacts
- influence replay/proof/CI/governance
"""

from __future__ import annotations

from typing import Tuple

from afritech.afripower.constants import (
    AFRIPOWER_PROJECTION_STATUS,
    DISPLAY_ONLY,
    ENTERPRISE_INTELLIGENCE_ONLY,
    LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
    PROJECTION_CREATES_AUTHORITY,
    PROJECTION_ONLY,
    READ_ONLY,
    REFERENCE_ONLY,
)


DASHBOARD_COMPONENT = "AFRIPowerDashboard"
DASHBOARD_COMPONENT_ID = "afritech.afripower.dashboard"
DASHBOARD_VERSION = "1.0"

DASHBOARD_STATUS = "OBSERVATIONAL_ONLY"
DASHBOARD_MODE = "READ_ONLY_ENTERPRISE_INTELLIGENCE_DASHBOARD"
DASHBOARD_PROJECTION_STATUS = AFRIPOWER_PROJECTION_STATUS

DASHBOARD_READ_ONLY = READ_ONLY
DASHBOARD_REFERENCE_ONLY = REFERENCE_ONLY
DASHBOARD_DISPLAY_ONLY = DISPLAY_ONLY
DASHBOARD_PROJECTION_ONLY = PROJECTION_ONLY
DASHBOARD_ENTERPRISE_INTELLIGENCE_ONLY = ENTERPRISE_INTELLIGENCE_ONLY

DASHBOARD_AUTHORITATIVE = False
DASHBOARD_CREATES_AUTHORITY = PROJECTION_CREATES_AUTHORITY
DASHBOARD_VALIDATES_TRUTH = False
DASHBOARD_EXECUTES_RUNTIME = False
DASHBOARD_MUTATES_ARTIFACTS = False
DASHBOARD_MUTATES_RECEIPTS = False
DASHBOARD_MUTATES_PROOFS = False
DASHBOARD_INFLUENCES_RUNTIME = False
DASHBOARD_INFLUENCES_REPLAY = False
DASHBOARD_INFLUENCES_PROOF = False
DASHBOARD_INFLUENCES_CI = False
DASHBOARD_INFLUENCES_GOVERNANCE = False

DASHBOARD_WIDGET_TYPES: Tuple[str, ...] = (
    "summary",
    "metric",
    "graph",
    "table",
    "insight",
    "receipt_reference",
    "proof_reference",
)

DASHBOARD_METRIC_TYPES: Tuple[str, ...] = (
    "node_count",
    "edge_count",
    "receipt_count",
    "proof_reference_count",
    "traceability_reference_count",
    "insight_count",
)

DASHBOARD_ALLOWED_OUTPUT_FORMATS: Tuple[str, ...] = (
    "dict",
    "json",
    "table",
)

DASHBOARD_METADATA = {
    "component": DASHBOARD_COMPONENT,
    "component_id": DASHBOARD_COMPONENT_ID,
    "version": DASHBOARD_VERSION,
    "status": DASHBOARD_STATUS,
    "mode": DASHBOARD_MODE,
    "projection_status": DASHBOARD_PROJECTION_STATUS,
    "read_only": DASHBOARD_READ_ONLY,
    "reference_only": DASHBOARD_REFERENCE_ONLY,
    "display_only": DASHBOARD_DISPLAY_ONLY,
    "projection_only": DASHBOARD_PROJECTION_ONLY,
    "enterprise_intelligence_only": DASHBOARD_ENTERPRISE_INTELLIGENCE_ONLY,
    "non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
    "consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    "authoritative": DASHBOARD_AUTHORITATIVE,
    "creates_authority": DASHBOARD_CREATES_AUTHORITY,
    "validates_truth": DASHBOARD_VALIDATES_TRUTH,
    "executes_runtime": DASHBOARD_EXECUTES_RUNTIME,
    "mutates_artifacts": DASHBOARD_MUTATES_ARTIFACTS,
    "mutates_receipts": DASHBOARD_MUTATES_RECEIPTS,
    "mutates_proofs": DASHBOARD_MUTATES_PROOFS,
    "influences_runtime": DASHBOARD_INFLUENCES_RUNTIME,
    "influences_replay": DASHBOARD_INFLUENCES_REPLAY,
    "influences_proof": DASHBOARD_INFLUENCES_PROOF,
    "influences_ci": DASHBOARD_INFLUENCES_CI,
    "influences_governance": DASHBOARD_INFLUENCES_GOVERNANCE,
}


def dashboard_metadata() -> dict[str, object]:
    """Return deterministic AFRIPower dashboard metadata."""

    return dict(DASHBOARD_METADATA)


def assert_dashboard_constants() -> None:
    """Fail closed if dashboard constants violate AFRIPower boundaries."""

    forbidden_true_flags = (
        DASHBOARD_AUTHORITATIVE,
        DASHBOARD_CREATES_AUTHORITY,
        DASHBOARD_VALIDATES_TRUTH,
        DASHBOARD_EXECUTES_RUNTIME,
        DASHBOARD_MUTATES_ARTIFACTS,
        DASHBOARD_MUTATES_RECEIPTS,
        DASHBOARD_MUTATES_PROOFS,
        DASHBOARD_INFLUENCES_RUNTIME,
        DASHBOARD_INFLUENCES_REPLAY,
        DASHBOARD_INFLUENCES_PROOF,
        DASHBOARD_INFLUENCES_CI,
        DASHBOARD_INFLUENCES_GOVERNANCE,
    )

    if any(forbidden_true_flags):
        raise RuntimeError("AFRIPower dashboard authority boundary violation")

    required_true_flags = (
        DASHBOARD_READ_ONLY,
        DASHBOARD_REFERENCE_ONLY,
        DASHBOARD_DISPLAY_ONLY,
        DASHBOARD_PROJECTION_ONLY,
        DASHBOARD_ENTERPRISE_INTELLIGENCE_ONLY,
    )

    if not all(required_true_flags):
        raise RuntimeError("AFRIPower dashboard safety boundary violation")


__all__ = [
    "DASHBOARD_COMPONENT",
    "DASHBOARD_COMPONENT_ID",
    "DASHBOARD_VERSION",
    "DASHBOARD_STATUS",
    "DASHBOARD_MODE",
    "DASHBOARD_PROJECTION_STATUS",
    "DASHBOARD_READ_ONLY",
    "DASHBOARD_REFERENCE_ONLY",
    "DASHBOARD_DISPLAY_ONLY",
    "DASHBOARD_PROJECTION_ONLY",
    "DASHBOARD_ENTERPRISE_INTELLIGENCE_ONLY",
    "DASHBOARD_AUTHORITATIVE",
    "DASHBOARD_CREATES_AUTHORITY",
    "DASHBOARD_VALIDATES_TRUTH",
    "DASHBOARD_EXECUTES_RUNTIME",
    "DASHBOARD_MUTATES_ARTIFACTS",
    "DASHBOARD_MUTATES_RECEIPTS",
    "DASHBOARD_MUTATES_PROOFS",
    "DASHBOARD_INFLUENCES_RUNTIME",
    "DASHBOARD_INFLUENCES_REPLAY",
    "DASHBOARD_INFLUENCES_PROOF",
    "DASHBOARD_INFLUENCES_CI",
    "DASHBOARD_INFLUENCES_GOVERNANCE",
    "DASHBOARD_WIDGET_TYPES",
    "DASHBOARD_METRIC_TYPES",
    "DASHBOARD_ALLOWED_OUTPUT_FORMATS",
    "DASHBOARD_METADATA",
    "dashboard_metadata",
    "assert_dashboard_constants",
]
