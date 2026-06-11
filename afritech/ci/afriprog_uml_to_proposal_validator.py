from __future__ import annotations

import sys

from afritech.design.uml import parse_uml, uml_to_proposal

VALIDATOR_NAME = "afritech.ci.afriprog_uml_to_proposal_validator"


def validate() -> None:
    model = parse_uml("Chicken\n- age\n- weight\n+ layEgg()", diagram_type="class")
    proposal = uml_to_proposal(model)
    if proposal.governance_required is not True:
        raise RuntimeError("UML proposal must require governance")
    if proposal.activation_allowed is not False:
        raise RuntimeError("UML proposal must not activate")
    if proposal.runtime_mutation_allowed is not False:
        raise RuntimeError("UML proposal must not mutate runtime")


def main() -> int:
    try:
        validate()
        print("Afriprog UML to proposal validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog UML to proposal validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
