"""Copilot-style Afriprog developer assistance.

The package provides suggestions, explanations, tests, fixtures, and rollback
plans as tooling outputs only. Validators, replay, contracts, and governance
remain the admission authorities.
"""

from afritech.extensions.afriprog.copilot_assist.context_collector import (
    collect_context,
)
from afritech.extensions.afriprog.copilot_assist.explanation_builder import (
    explain_code,
)
from afritech.extensions.afriprog.copilot_assist.safety_classifier import (
    classify_suggestion,
)
from afritech.extensions.afriprog.copilot_assist.suggestion_engine import (
    generate_suggestion,
)
from afritech.extensions.afriprog.copilot_assist.suggestion_model import (
    ASSISTANCE_KINDS,
    CopilotSuggestion,
)
from afritech.extensions.afriprog.copilot_assist.validation_gate import (
    validate_suggestion_gate,
)
from afritech.extensions.afriprog.copilot_assist.proposal_intelligence import (
    ContextAwareToolingProposal,
    emit_governance_ready_proposal,
    generate_context_aware_proposal,
    inspect_context_proposal,
    validate_context_proposal,
)

__all__ = [
    "ASSISTANCE_KINDS",
    "CopilotSuggestion",
    "ContextAwareToolingProposal",
    "classify_suggestion",
    "collect_context",
    "emit_governance_ready_proposal",
    "explain_code",
    "generate_context_aware_proposal",
    "generate_suggestion",
    "inspect_context_proposal",
    "validate_context_proposal",
    "validate_suggestion_gate",
]
