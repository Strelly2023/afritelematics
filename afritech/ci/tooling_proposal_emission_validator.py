"""Validate that AfriProgramming tooling emits proposal artifacts only."""

from __future__ import annotations

import sys

from afritech.afriprogramming.proposals import (
    PROPOSAL_SCHEMA,
    emit_tooling_proposal,
    evaluate_mutation_request,
    validate_proposal,
)


VALIDATOR_NAME = "afritech.ci.tooling_proposal_emission_validator"


class ToolingProposalEmissionValidationError(RuntimeError):
    """Raised when proposal emission stops being safe."""


def fail(message: str) -> None:
    raise ToolingProposalEmissionValidationError(message)


def validate_tooling_proposal_emission() -> None:
    proposal = emit_tooling_proposal(
        origin="ai_constraint_engine",
        actor="ai",
        intent="Suggest driver API tooling update",
        change_type="tooling_change",
        target="afritech/afriprogramming/tooling_surfaces.py",
        diff='{"op":"replace","path":"/example","value":"proposal-only"}',
    )
    payload = proposal.canonical_dict()

    if payload["schema"] != PROPOSAL_SCHEMA:
        fail("proposal schema mismatch")
    if payload["validation"]["status"] != "pending":
        fail("proposal must start validation-pending")
    if payload["governance"]["status"] != "pending":
        fail("proposal must start governance-pending")
    if payload["activation"]["status"] != "blocked":
        fail("proposal must start activation-blocked")
    if len(payload["proposal_hash"]) != 64:
        fail("proposal hash must be SHA-256 length")

    validated = validate_proposal(proposal)
    if validated.validation.status != "pass":
        fail("safe tooling proposal should pass proposal validation")

    blocked = evaluate_mutation_request(None)
    if blocked["mutation_allowed"] is not False:
        fail("mutation request without proposal must be blocked")

    protected = emit_tooling_proposal(
        origin="ai_constraint_engine",
        actor="ai",
        intent="Attempt protected mutation",
        change_type="tooling_change",
        target="afritech/governance/INDEX.yaml",
        diff='{"op":"replace","path":"/x","value":"unsafe"}',
    )
    protected_validated = validate_proposal(protected)
    if protected_validated.validation.status != "fail":
        fail("protected target proposal must fail validation")


def main() -> int:
    try:
        validate_tooling_proposal_emission()
        print("Tooling proposal emission validation PASSED")
        return 0
    except Exception as exc:
        print(f"Tooling proposal emission validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
