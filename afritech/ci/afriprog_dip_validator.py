from __future__ import annotations

import sys

from afritech.design.solid import validate_dip


def validate() -> None:
    passing = validate_dip(({"consumer": "FeedingService", "dependency_type": "interface"},))
    if passing["valid"] is not True:
        raise RuntimeError(f"abstract dependency rejected: {passing}")

    failing = validate_dip(({"consumer": "FeedingService", "dependency_type": "concrete"},))
    if failing["valid"] is not False:
        raise RuntimeError("concrete dependency was admitted")


def main() -> int:
    try:
        validate()
        print("Afriprog DIP validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog DIP validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
