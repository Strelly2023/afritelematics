from __future__ import annotations

import sys

from afritech.design.solid import validate_srp


def validate() -> None:
    passing = validate_srp(({"name": "FeedingService", "responsibilities": ("feeding",)},))
    if passing["valid"] is not True:
        raise RuntimeError(f"SRP-compliant module rejected: {passing}")

    failing = validate_srp(({"name": "FarmService", "responsibilities": ("feeding", "finance")},))
    if failing["valid"] is not False:
        raise RuntimeError("multi-responsibility module was admitted")


def main() -> int:
    try:
        validate()
        print("Afriprog SRP validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog SRP validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
