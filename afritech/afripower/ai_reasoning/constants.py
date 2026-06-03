"""
AFRIPower AI reasoning constants.

AFRIPower AI reasoning is interpretive and observational only.

It may:
- summarize existing references
- generate explanatory insights
- organize reasoning views
- support human review

It must not:
- execute runtime behavior
- validate truth
- create authority
- mutate artifacts
- decide admissibility
- influence replay/proof/CI/governance
"""

from __future__ import annotations

from typing import Tuple

from afritech.afripower.constants import (
    DISPLAY_ONLY,
    ENTERPRISE_INTELLIGENCE_ONLY,
    INTERPRETIVE_ONLY,
    LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
    OBSERVATIONAL_ONLY,
    PROJECTION_CREATES_AUTHORITY,
    PROJECTION_ONLY,
    READ_ONLY,
    REFERENCE_ONLY,
)


AI_REASONING_COMPONENT = "AFRIPowerAIReasoning"
AI_REASONING_COMPONENT_ID = "afritech.afripower.ai_reasoning"
AI_REASONING_VERSION = "1.0"

AI_REASONING_STATUS = "INTERPRETIVE_OBSERVATIONAL_ONLY"
AI_REASONING_MODE = "READ_ONLY_ENTERPRISE_INTELLIGENCE_REASONING"

AI_REASONING_READ_ONLY = READ_ONLY
AI_REASONING_REFERENCE_ONLY = REFERENCE_ONLY
AI_REASONING_DISPLAY_ONLY = DISPLAY_ONLY
AI_REASONING_PROJECTION_ONLY = PROJECTION_ONLY
AI_REASONING_OBSERVATIONAL_ONLY = OBSERVATIONAL_ONLY
AI_REASONING_INTERPRETIVE_ONLY = INTERPRETIVE_ONLY
AI_REASONING_ENTERPRISE_INTELLIGENCE_ONLY = ENTERPRISE_INTELLIGENCE_ONLY

AI_REASONING_AUTHORITATIVE = False
AI_REASONING_CREATES_AUTHORITY = PROJECTION_CREATES_AUTHORITY
AI_REASONING_VALIDATES_TRUTH = False
AI_REASONING_EXECUTES_RUNTIME = False
AI_REASONING_MUTATES_ARTIFACTS = False
AI_REASONING_DECIDES_ADMISSIBILITY = False
AI_REASONING_INFLUENCES_RUNTIME = False
AI_REASONING_INFLUENCES_REPLAY = False
AI_REASONING_INFLUENCES_PROOF = False
AI_REASONING_INFLUENCES_CI = False
AI_REASONING_INFLUENCES_GOVERNANCE = False

AI_REASONING_INPUT_TYPES: Tuple[str, ...] = (
    "graph_summary",
    "dashboard_metrics",
    "receipt_reference",
    "proof_reference",
    "traceability_reference",
    "projection_payload",
)

AI_REASONING_OUTPUT_TYPES: Tuple[str, ...] = (
    "summary",
    "explanation",
    "insight",
    "observation",
    "recommendation_for_human_review",
)

AI_REASONING_FORBIDDEN_OUTPUT_TYPES: Tuple[str, ...] = (
    "authority_decision",
    "truth_validation",
    "runtime_command",
    "governance_decision",
    "admissibility_decision",
    "proof_verdict",
    "ci_verdict",
)

AI_REASONING_METADATA = {
    "component": AI_REASONING_COMPONENT,
    "component_id": AI_REASONING_COMPONENT_ID,
    "version": AI_REASONING_VERSION,
    "status": AI_REASONING_STATUS,
    "mode": AI_REASONING_MODE,
    "read_only": AI_REASONING_READ_ONLY,
    "reference_only": AI_REASONING_REFERENCE_ONLY,
    "display_only": AI_REASONING_DISPLAY_ONLY,
    "projection_only": AI_REASONING_PROJECTION_ONLY,
    "observational_only": AI_REASONING_OBSERVATIONAL_ONLY,
    "interpretive_only": AI_REASONING_INTERPRETIVE_ONLY,
    "enterprise_intelligence_only": AI_REASONING_ENTERPRISE_INTELLIGENCE_ONLY,
    "non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
    "consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    "authoritative": AI_REASONING_AUTHORITATIVE,
    "creates_authority": AI_REASONING_CREATES_AUTHORITY,
    "validates_truth": AI_REASONING_VALIDATES_TRUTH,
    "executes_runtime": AI_REASONING_EXECUTES_RUNTIME,
    "mutates_artifacts": AI_REASONING_MUTATES_ARTIFACTS,
    "decides_admissibility": AI_REASONING_DECIDES_ADMISSIBILITY,
    "influences_runtime": AI_REASONING_INFLUENCES_RUNTIME,
    "influences_replay": AI_REASONING_INFLUENCES_REPLAY,
    "influences_proof": AI_REASONING_INFLUENCES_PROOF,
    "influences_ci": AI_REASONING_INFLUENCES_CI,
    "influences_governance": AI_REASONING_INFLUENCES_GOVERNANCE,
}


def ai_reasoning_metadata() -> dict[str, object]:
    """Return deterministic AFRIPower AI reasoning metadata."""

    return dict(AI_REASONING_METADATA)


def assert_ai_reasoning_constants() -> None:
    """Fail closed if AI reasoning constants violate AFRIPower boundaries."""

    forbidden_true_flags = (
        AI_REASONING_AUTHORITATIVE,
        AI_REASONING_CREATES_AUTHORITY,
        AI_REASONING_VALIDATES_TRUTH,
        AI_REASONING_EXECUTES_RUNTIME,
        AI_REASONING_MUTATES_ARTIFACTS,
        AI_REASONING_DECIDES_ADMISSIBILITY,
        AI_REASONING_INFLUENCES_RUNTIME,
        AI_REASONING_INFLUENCES_REPLAY,
        AI_REASONING_INFLUENCES_PROOF,
        AI_REASONING_INFLUENCES_CI,
        AI_REASONING_INFLUENCES_GOVERNANCE,
    )

    if any(forbidden_true_flags):
        raise RuntimeError("AFRIPower AI reasoning authority boundary violation")

    required_true_flags = (
        AI_REASONING_READ_ONLY,
        AI_REASONING_REFERENCE_ONLY,
        AI_REASONING_DISPLAY_ONLY,
        AI_REASONING_PROJECTION_ONLY,
        AI_REASONING_OBSERVATIONAL_ONLY,
        AI_REASONING_INTERPRETIVE_ONLY,
        AI_REASONING_ENTERPRISE_INTELLIGENCE_ONLY,
    )

    if not all(required_true_flags):
        raise RuntimeError("AFRIPower AI reasoning safety boundary violation")


__all__ = [
    "AI_REASONING_COMPONENT",
    "AI_REASONING_COMPONENT_ID",
    "AI_REASONING_VERSION",
    "AI_REASONING_STATUS",
    "AI_REASONING_MODE",
    "AI_REASONING_READ_ONLY",
    "AI_REASONING_REFERENCE_ONLY",
    "AI_REASONING_DISPLAY_ONLY",
    "AI_REASONING_PROJECTION_ONLY",
    "AI_REASONING_OBSERVATIONAL_ONLY",
    "AI_REASONING_INTERPRETIVE_ONLY",
    "AI_REASONING_ENTERPRISE_INTELLIGENCE_ONLY",
    "AI_REASONING_AUTHORITATIVE",
    "AI_REASONING_CREATES_AUTHORITY",
    "AI_REASONING_VALIDATES_TRUTH",
    "AI_REASONING_EXECUTES_RUNTIME",
    "AI_REASONING_MUTATES_ARTIFACTS",
    "AI_REASONING_DECIDES_ADMISSIBILITY",
    "AI_REASONING_INFLUENCES_RUNTIME",
    "AI_REASONING_INFLUENCES_REPLAY",
    "AI_REASONING_INFLUENCES_PROOF",
    "AI_REASONING_INFLUENCES_CI",
    "AI_REASONING_INFLUENCES_GOVERNANCE",
    "AI_REASONING_INPUT_TYPES",
    "AI_REASONING_OUTPUT_TYPES",
    "AI_REASONING_FORBIDDEN_OUTPUT_TYPES",
    "AI_REASONING_METADATA",
    "ai_reasoning_metadata",
    "assert_ai_reasoning_constants",
]
