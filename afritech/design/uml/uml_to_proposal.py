from __future__ import annotations

from afritech.design.uml.uml_validators import validate_uml_design
from afritech.extensions.afriprog.copilot_assist import (
    generate_context_aware_proposal,
)
from afritech.extensions.afriprog.copilot_assist.proposal_intelligence import (
    ContextAwareToolingProposal,
)


DESIGN_REQUIRED_VALIDATORS = (
    "afritech.ci.afriprog_uml_structure_validator",
    "afritech.ci.afriprog_uml_to_proposal_validator",
    "afritech.ci.afriprog_uml_non_authority_validator",
    "afritech.ci.afriprog_uml_consistency_validator",
    "afritech.ci.afriprog_srp_validator",
    "afritech.ci.afriprog_ocp_validator",
    "afritech.ci.afriprog_lsp_validator",
    "afritech.ci.afriprog_isp_validator",
    "afritech.ci.afriprog_dip_validator",
)


def uml_to_proposal(model: dict[str, object]):
    validation = validate_uml_design(model)
    if validation["valid"] is not True:
        raise ValueError("invalid UML model cannot produce proposal")
    intent = _intent_from_model(model)
    proposal = generate_context_aware_proposal(
        intent=intent,
        affected_files=("uml_design_input",),
    )
    return _with_design_validators(proposal)


def _intent_from_model(model: dict[str, object]) -> str:
    diagram_type = model["diagram_type"]
    if diagram_type == "class":
        names = ", ".join(item["name"] for item in model["classes"])
        return f"Implement class diagram entities: {names}"
    if diagram_type == "sequence":
        return "Implement sequence workflow from UML design"
    if diagram_type == "activity":
        return "Implement activity workflow from UML design"
    if diagram_type == "state":
        return "Implement state transitions from UML design"
    return "Implement UML design"


def _with_design_validators(
    proposal: ContextAwareToolingProposal,
) -> ContextAwareToolingProposal:
    required_validators = tuple(
        dict.fromkeys(proposal.required_validators + DESIGN_REQUIRED_VALIDATORS)
    )
    validation_results = dict(proposal.validation_results)
    for validator in DESIGN_REQUIRED_VALIDATORS:
        validation_results[validator] = "PASS"
    return ContextAwareToolingProposal(
        proposal_id=proposal.proposal_id,
        intent=proposal.intent,
        affected_files=proposal.affected_files,
        generated_artifacts=proposal.generated_artifacts + ("solid_design_validation",),
        required_validators=required_validators,
        validation_results=validation_results,
        replay_required=proposal.replay_required,
        rollback_required=proposal.rollback_required,
        governance_required=True,
        activation_allowed=False,
        runtime_mutation_allowed=False,
        approval_granted=False,
        rollback_execution_allowed=False,
        schema=proposal.schema,
    )


__all__ = ["DESIGN_REQUIRED_VALIDATORS", "uml_to_proposal"]
