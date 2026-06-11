from __future__ import annotations

import sys

from afritech.design.uml import parse_uml, validate_uml_design

VALIDATOR_NAME = "afritech.ci.afriprog_uml_structure_validator"


def validate() -> None:
    cases = (
        ("class", "Customer\n- name\n- email\n+ placeOrder()"),
        ("sequence", "User -> OrderService: placeOrder"),
        ("activity", "Collect Eggs -> Sort -> Store -> Sell"),
        ("state", "Pending -> Paid\nPaid -> Shipped"),
    )
    for diagram_type, source in cases:
        model = parse_uml(source, diagram_type=diagram_type)
        result = validate_uml_design(model)
        if result["valid"] is not True:
            raise RuntimeError(f"{diagram_type} UML should validate: {result}")


def main() -> int:
    try:
        validate()
        print("Afriprog UML structure validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog UML structure validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
