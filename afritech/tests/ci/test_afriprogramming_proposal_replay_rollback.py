from __future__ import annotations

import subprocess
import sys

import pytest

from afritech.afriprogramming.proposals import (
    ToolingProposalError,
    activation_gate,
    approve_proposal,
    build_activation_record,
    build_rollback_plan,
    complete_proposal_lifecycle,
    emit_tooling_proposal,
    evaluate_rollback_execution_request,
    replay_activation_record,
    validate_proposal,
    validate_rollback_plan,
)
from afritech.ci import (
    proposal_lifecycle_completion_validator,
    proposal_replay_record_validator,
    proposal_rollback_readiness_validator,
)


VALIDATORS = (
    proposal_replay_record_validator,
    proposal_rollback_readiness_validator,
    proposal_lifecycle_completion_validator,
)


def _ready_proposal():
    proposal = emit_tooling_proposal(
        origin="afriprogramming_cli",
        actor="user",
        intent="Replay and rollback tooling proposal",
        change_type="tooling_change",
        target="afritech/afriprogramming/tooling_surfaces.py",
        diff='{"op":"replace","path":"/status","value":"new"}',
    )
    return activation_gate(
        approve_proposal(
            validate_proposal(proposal),
            approved_by=("governance-council",),
            timestamp="2026-06-06T00:00:00Z",
            approval_ref="GOV-REPLAY-ROLLBACK",
        ),
        timestamp="2026-06-06T00:00:01Z",
    )


def test_activation_record_replays_deterministically():
    record = build_activation_record(
        _ready_proposal(),
        pre_state={"status": "old", "version": "v1"},
        post_state={"status": "new", "version": "v1"},
        applied_diff=({"op": "replace", "path": "/status", "value": "new"},),
        timestamp="2026-06-06T00:00:02Z",
    )

    assert replay_activation_record(record) is True
    assert len(record.replay_hash) == 64
    assert record.governance_reference == "GOV-REPLAY-ROLLBACK"


def test_activation_record_rejects_non_replayable_diff():
    with pytest.raises(ToolingProposalError):
        build_activation_record(
            _ready_proposal(),
            pre_state={"status": "old"},
            post_state={"status": "new"},
            applied_diff=({"op": "replace", "path": "/other", "value": "new"},),
            timestamp="2026-06-06T00:00:02Z",
        )


def test_rollback_plan_replays_to_pre_state_but_does_not_execute():
    record = build_activation_record(
        _ready_proposal(),
        pre_state={"mode": "proposal", "version": "v1"},
        post_state={"mode": "governed", "version": "v1"},
        applied_diff=({"op": "replace", "path": "/mode", "value": "governed"},),
        timestamp="2026-06-06T00:00:02Z",
    )
    plan = validate_rollback_plan(record, build_rollback_plan(record))
    lifecycle = complete_proposal_lifecycle(record, plan)

    assert plan.validated is True
    assert lifecycle.status == "complete"
    assert lifecycle.rollback_execution_performed is False

    blocked = evaluate_rollback_execution_request(
        lifecycle,
        governance_approved=False,
    )
    approved_but_protected = evaluate_rollback_execution_request(
        lifecycle,
        governance_approved=True,
    )

    assert blocked["rollback_allowed"] is False
    assert blocked["reason"] == "governance approval required"
    assert approved_but_protected["rollback_allowed"] is False
    assert approved_but_protected["rollback_ready"] is True


def test_lifecycle_completion_requires_validated_rollback_plan():
    record = build_activation_record(
        _ready_proposal(),
        pre_state={"lifecycle": "ready"},
        post_state={"lifecycle": "complete"},
        applied_diff=({"op": "replace", "path": "/lifecycle", "value": "complete"},),
        timestamp="2026-06-06T00:00:02Z",
    )
    plan = build_rollback_plan(record)

    with pytest.raises(ToolingProposalError):
        complete_proposal_lifecycle(record, plan)


def test_proposal_replay_rollback_validators_pass_directly():
    proposal_replay_record_validator.validate_proposal_replay_record()
    proposal_rollback_readiness_validator.validate_proposal_rollback_readiness()
    proposal_lifecycle_completion_validator.validate_proposal_lifecycle_completion()


def test_proposal_replay_rollback_validator_cli_entrypoints_pass():
    for validator in VALIDATORS:
        result = subprocess.run(
            [sys.executable, "-m", validator.VALIDATOR_NAME],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASSED" in result.stdout
