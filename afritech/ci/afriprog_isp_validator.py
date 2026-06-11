from __future__ import annotations

import sys

from afritech.design.solid import validate_isp


def validate() -> None:
    passing = validate_isp(({"name": "Feeder", "unused_methods": ()},))
    if passing["valid"] is not True:
        raise RuntimeError(f"segregated interface rejected: {passing}")

    failing = validate_isp(({"name": "Feeder", "unused_methods": ("collectEggs",)},))
    if failing["valid"] is not False:
        raise RuntimeError("fat interface was admitted")


def main() -> int:
    try:
        validate()
        print("Afriprog ISP validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog ISP validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
