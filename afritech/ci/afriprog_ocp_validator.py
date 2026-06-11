from __future__ import annotations

import sys

from afritech.design.solid import validate_ocp


def validate() -> None:
    passing = validate_ocp(({"name": "IoTFeeding", "type": "domain_model", "mode": "extension"},))
    if passing["valid"] is not True:
        raise RuntimeError(f"extension-safe change rejected: {passing}")

    failing = validate_ocp(({"name": "runtime_gate", "type": "runtime", "mode": "modification"},))
    if failing["valid"] is not False:
        raise RuntimeError("protected core modification was admitted")


def main() -> int:
    try:
        validate()
        print("Afriprog OCP validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog OCP validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
