from __future__ import annotations

import sys

from afritech.design.uml import parse_uml, validate_uml_design

VALIDATOR_NAME = "afritech.ci.afriprog_uml_non_authority_validator"


def validate() -> None:
    model = parse_uml("Order: Pending -> Paid", diagram_type="state")
    result = validate_uml_design(model)
    if result["activation_allowed"] is not False:
        raise RuntimeError("UML must not allow activation")
    if result["runtime_mutation_allowed"] is not False:
        raise RuntimeError("UML must not mutate runtime")
    if result["governance_required"] is not True:
        raise RuntimeError("UML proposal flow must require governance")


def main() -> int:
    try:
        validate()
        print("Afriprog UML non-authority validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog UML non-authority validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
