from __future__ import annotations

import subprocess
import sys

from afritech.extensions.afriprog.copilot_assist import (
    emit_governance_ready_proposal,
    generate_context_aware_proposal,
    inspect_context_proposal,
    validate_context_proposal,
)
from afritech.ci import (
    afriprog_activation_boundary_validator,
    afriprog_auto_validation_loop_validator,
    afriprog_context_proposal_validator,
    afriprog_governance_readiness_validator,
    afriprog_tooling_proposal_non_authority_validator,
)


VALIDATORS = (
    afriprog_context_proposal_validator,
    afriprog_auto_validation_loop_validator,
    afriprog_tooling_proposal_non_authority_validator,
    afriprog_governance_readiness_validator,
    afriprog_activation_boundary_validator,
)


def test_context_aware_proposal_is_governance_ready_not_authoritative():
    proposal = generate_context_aware_proposal(
        intent="add driver availability endpoint",
        affected_files=("afritech/api/driver.py",),
    )
    inspected = inspect_context_proposal(proposal)
    validation = validate_context_proposal(proposal)
    emitted = emit_governance_ready_proposal(proposal)

    assert inspected["governance_review_required"] is True
    assert inspected["activation_allowed"] is False
    assert inspected["runtime_mutation_allowed"] is False
    assert validation["status"] == "ready_for_governance"
    assert validation["approval_granted"] is False
    assert emitted["emitted"] is True
    assert emitted["activation_allowed"] is False


def test_context_aware_proposal_cli_commands_are_non_authoritative():
    commands = (
        ("propose", "add driver availability endpoint"),
        ("propose", "fix validator", "--from-failure", "validator failed"),
        ("proposal-inspect", "proposal-123"),
        ("proposal-validate", "proposal-123"),
        ("proposal-emit", "proposal-123"),
    )
    for command in commands:
        result = subprocess.run(
            [sys.executable, "-m", "afritech.cli.main", *command, "--json"],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert '"activation_allowed": false' in result.stdout
        assert '"runtime_mutation_allowed": false' in result.stdout


def test_context_proposal_validators_pass_directly():
    afriprog_context_proposal_validator.validate_context_proposal_surface()
    afriprog_auto_validation_loop_validator.validate_auto_validation_loop()
    afriprog_tooling_proposal_non_authority_validator.validate_tooling_proposal_non_authority()
    afriprog_governance_readiness_validator.validate_governance_readiness()
    afriprog_activation_boundary_validator.validate_activation_boundary()


def test_context_proposal_validator_cli_entrypoints_pass():
    for validator in VALIDATORS:
        result = subprocess.run(
            [sys.executable, "-m", validator.VALIDATOR_NAME],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASSED" in result.stdout
