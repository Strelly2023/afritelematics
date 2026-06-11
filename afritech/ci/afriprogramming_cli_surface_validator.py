"""Validate AfriProgramming CLI as developer tooling only."""

from __future__ import annotations

import sys

from afritech.afriprogramming.tooling_surfaces import build_cli_surface_catalog
from afritech.ci.afriprogramming_tooling_surface_common import (
    fail,
    validate_tooling_behavior,
)


VALIDATOR_NAME = "afritech.ci.afriprogramming_cli_surface_validator"


def validate_afriprogramming_cli_surface() -> None:
    def behavior() -> None:
        catalog = build_cli_surface_catalog()
        if catalog["developer_tooling_only"] is not True:
            fail("AfriProgramming CLI must remain developer tooling only")
        if catalog["validators_remain_final"] is not True:
            fail("AfriProgramming CLI must preserve validator authority")

    validate_tooling_behavior("afriprogramming_cli", VALIDATOR_NAME, behavior)


def main() -> int:
    try:
        validate_afriprogramming_cli_surface()
        print("AfriProgramming CLI surface validation PASSED")
        return 0
    except Exception as exc:
        print(f"AfriProgramming CLI surface validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
