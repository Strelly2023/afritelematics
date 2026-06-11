"""Validate the AfriProg to AfriProgramming governed boundary."""

from __future__ import annotations

from afritech.afriprogramming.integration import (
    build_afriprog_boundary_profile,
    integrate_context_proposal,
)
from afritech.extensions.afriprog.copilot_assist import generate_context_aware_proposal


VALIDATOR_NAME = "afritech.ci.afriprog_afriprogramming_boundary_validator"


def _fail(message: str) -> None:
    raise RuntimeError(message)


def validate_afriprog_afriprogramming_boundary() -> None:
    profile = build_afriprog_boundary_profile()
    if profile.handoff_mode != "proposal_only":
        _fail("AfriProg handoff must remain proposal-only")
    if profile.truth_authority_transferred:
        _fail("AfriProg must not transfer truth authority")
    if profile.runtime_mutation_allowed:
        _fail("AfriProg boundary must not allow runtime mutation")

    proposal = generate_context_aware_proposal(
        intent="prepare governed validator update",
        affected_files=("afritech/afriprogramming/tooling_surfaces.py",),
    )
    integration = integrate_context_proposal(proposal)
    if integration.source_validation_status != "ready_for_governance":
        _fail("AfriProg source proposal must be governance-ready")
    if integration.target_validation_status != "pass":
        _fail("AfriProgramming target proposal must validate cleanly")
    if integration.activation_allowed:
        _fail("boundary integration must not activate changes")
    if integration.runtime_mutation_allowed:
        _fail("boundary integration must not mutate runtime")
    if not integration.governance_required or not integration.replay_required:
        _fail("boundary integration must require governance and replay")


def main() -> int:
    validate_afriprog_afriprogramming_boundary()
    print("AfriProg to AfriProgramming boundary validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
