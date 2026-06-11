"""Validate proposal activation records are deterministic and replayable."""

from __future__ import annotations

import sys

from afritech.afriprogramming.proposals import (
    approve_proposal,
    build_activation_record,
    emit_tooling_proposal,
    replay_activation_record,
    validate_proposal,
)


VALIDATOR_NAME = "afritech.ci.proposal_replay_record_validator"


class ProposalReplayRecordValidationError(RuntimeError):
    """Raised when proposal replay records regress."""


def fail(message: str) -> None:
    raise ProposalReplayRecordValidationError(message)


def _activation_ready_proposal():
    from afritech.afriprogramming.proposals import activation_gate

    proposal = emit_tooling_proposal(
        origin="afriprogramming_cli",
        actor="user",
        intent="Replay-recorded tooling change",
        change_type="tooling_change",
        target="afritech/afriprogramming/tooling_surfaces.py",
        diff='{"op":"replace","path":"/status","value":"proposal-only"}',
    )
    validated = validate_proposal(proposal)
    approved = approve_proposal(
        validated,
        approved_by=("governance-council",),
        timestamp="2026-06-06T00:00:00Z",
        approval_ref="GOV-REPLAY-001",
    )
    return activation_gate(approved, timestamp="2026-06-06T00:00:01Z")


def validate_proposal_replay_record() -> None:
    proposal = _activation_ready_proposal()
    pre_state = {"status": "old", "version": "v1"}
    diff = ({"op": "replace", "path": "/status", "value": "new"},)
    post_state = {"status": "new", "version": "v1"}

    record = build_activation_record(
        proposal,
        pre_state=pre_state,
        post_state=post_state,
        applied_diff=diff,
        timestamp="2026-06-06T00:00:02Z",
    )

    if replay_activation_record(record) is not True:
        fail("activation record must replay deterministically")
    if record.validator_status != "PASS":
        fail("activation record must retain validator PASS status")
    if record.governance_reference != "GOV-REPLAY-001":
        fail("activation record must retain governance reference")
    if len(record.replay_hash) != 64:
        fail("activation record replay hash must be SHA-256 length")


def main() -> int:
    try:
        validate_proposal_replay_record()
        print("Proposal replay record validation PASSED")
        return 0
    except Exception as exc:
        print(f"Proposal replay record validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
