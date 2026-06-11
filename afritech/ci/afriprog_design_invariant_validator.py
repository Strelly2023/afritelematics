from __future__ import annotations

import sys

from afritech.design.uml import parse_uml, uml_to_proposal, validate_uml_design
from afritech.design.uml.uml_to_proposal import DESIGN_REQUIRED_VALIDATORS
from afritech.extensions.afriprog.copilot_assist import validate_context_proposal


INVARIANT_ID = "INV-AFRIPROG-DESIGN-001"


def validate() -> None:
    model = parse_uml("Farm\n- name\nChicken\n- age\n+ layEgg()", diagram_type="class")
    design_validation = validate_uml_design(model)
    if design_validation["valid"] is not True:
        raise RuntimeError(f"{INVARIANT_ID}: UML-derived design must validate")
    if design_validation["solid_validation"]["valid"] is not True:
        raise RuntimeError(f"{INVARIANT_ID}: UML-derived design must pass SOLID checks")

    proposal = uml_to_proposal(model)
    payload = proposal.canonical_dict()
    required = set(payload["required_validators"])
    missing = tuple(sorted(set(DESIGN_REQUIRED_VALIDATORS) - required))
    if missing:
        raise RuntimeError(f"{INVARIANT_ID}: proposal missing design validators: {missing}")
    if payload["replay_required"] is not True:
        raise RuntimeError(f"{INVARIANT_ID}: UML-derived proposal must require replay")
    if payload["rollback_required"] is not True:
        raise RuntimeError(f"{INVARIANT_ID}: UML-derived proposal must require rollback readiness")
    if payload["governance_required"] is not True:
        raise RuntimeError(f"{INVARIANT_ID}: UML-derived proposal must require governance")
    if payload["activation_allowed"] is not False:
        raise RuntimeError(f"{INVARIANT_ID}: UML-derived proposal must not activate")
    if payload["runtime_mutation_allowed"] is not False:
        raise RuntimeError(f"{INVARIANT_ID}: UML-derived proposal must not mutate runtime")

    proposal_validation = validate_context_proposal(proposal)
    if proposal_validation["status"] != "ready_for_governance":
        raise RuntimeError(f"{INVARIANT_ID}: UML-derived proposal must be governance-ready")
    if proposal_validation["activation_allowed"] is not False:
        raise RuntimeError(f"{INVARIANT_ID}: proposal validation must not allow activation")


def main() -> int:
    try:
        validate()
        print(f"{INVARIANT_ID} validation PASSED")
        return 0
    except Exception as exc:
        print(f"{INVARIANT_ID} validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
