"""Validate the AI constraint engine as advisory generation only."""

from __future__ import annotations

import sys

from afritech.afriprogramming.tooling_surfaces import build_ai_constraint_request
from afritech.ci.afriprogramming_tooling_surface_common import (
    fail,
    validate_tooling_behavior,
)


VALIDATOR_NAME = "afritech.ci.ai_constraint_engine_validator"


def validate_ai_constraint_engine() -> None:
    def behavior() -> None:
        request = build_ai_constraint_request("driver endpoint")
        if request["accepted_without_validation"] is not False:
            fail("AI output must not be accepted without validation")
        if request["may_generate"] is not True:
            fail("AI constraint engine must be able to generate suggestions")

    validate_tooling_behavior("ai_constraint_engine", VALIDATOR_NAME, behavior)


def main() -> int:
    try:
        validate_ai_constraint_engine()
        print("AI constraint engine validation PASSED")
        return 0
    except Exception as exc:
        print(f"AI constraint engine validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
