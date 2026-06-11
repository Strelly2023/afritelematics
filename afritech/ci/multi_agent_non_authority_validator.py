"""Validate multi-agent orchestration as non-authoritative coordination."""

from __future__ import annotations

import sys

from afritech.afriprogramming.tooling_surfaces import build_multi_agent_plan
from afritech.ci.afriprogramming_tooling_surface_common import (
    fail,
    validate_tooling_behavior,
)


VALIDATOR_NAME = "afritech.ci.multi_agent_non_authority_validator"


def validate_multi_agent_non_authority() -> None:
    def behavior() -> None:
        plan = build_multi_agent_plan("repair contract mismatch")
        if plan["authority"] != "non_authoritative":
            fail("multi-agent orchestrator must remain non-authoritative")
        if plan["may_apply_changes"] is not False:
            fail("multi-agent orchestrator must not apply protected changes")
        if plan["must_submit_to_validators"] is not True:
            fail("multi-agent output must submit to validators")

    validate_tooling_behavior("multi_agent_orchestrator", VALIDATOR_NAME, behavior)


def main() -> int:
    try:
        validate_multi_agent_non_authority()
        print("Multi-agent non-authority validation PASSED")
        return 0
    except Exception as exc:
        print(f"Multi-agent non-authority validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
