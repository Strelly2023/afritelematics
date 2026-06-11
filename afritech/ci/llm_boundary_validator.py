"""Validate LLM connector boundaries."""

from __future__ import annotations

import sys

from afritech.afriprogramming.tooling_surfaces import build_llm_envelope
from afritech.ci.afriprogramming_tooling_surface_common import (
    fail,
    validate_tooling_behavior,
)


VALIDATOR_NAME = "afritech.ci.llm_boundary_validator"


def validate_llm_boundary() -> None:
    def behavior() -> None:
        envelope = build_llm_envelope("explain replay failure")
        if envelope["network_call_performed"] is not False:
            fail("LLM boundary validation must not require network calls")
        if envelope["model_output_trusted"] is not False:
            fail("LLM output must not be trusted as authority")
        if envelope["requires_validator_admission"] is not True:
            fail("LLM output must require validator admission")

    validate_tooling_behavior("llm_connector", VALIDATOR_NAME, behavior)


def main() -> int:
    try:
        validate_llm_boundary()
        print("LLM boundary validation PASSED")
        return 0
    except Exception as exc:
        print(f"LLM boundary validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
