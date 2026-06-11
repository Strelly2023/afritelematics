from __future__ import annotations

import sys

from afritech.design.uml import parse_uml, validate_uml_design

VALIDATOR_NAME = "afritech.ci.afriprog_uml_consistency_validator"


def validate() -> None:
    invalid = parse_uml("", diagram_type="class")
    result = validate_uml_design(invalid)
    if result["valid"] is not False:
        raise RuntimeError("empty class diagram must be invalid")
    if "class diagram must define at least one class" not in result["violations"]:
        raise RuntimeError("empty class diagram violation missing")


def main() -> int:
    try:
        validate()
        print("Afriprog UML consistency validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog UML consistency validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
