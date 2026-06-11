from __future__ import annotations

import subprocess
import sys

import pytest

from afritech.afriprogramming.proposals import (
    PROPOSAL_SCHEMA,
    ToolingProposalError,
    activation_gate,
    approve_proposal,
    emit_tooling_proposal,
    evaluate_mutation_request,
    reject_proposal,
    validate_proposal,
)
from afritech.ci import (
    governance_approval_flow_validator,
    tooling_activation_gate_validator,
    tooling_proposal_emission_validator,
)


VALIDATORS = (
    tooling_proposal_emission_validator,
    governance_approval_flow_validator,
    tooling_activation_gate_validator,
)


def test_tooling_proposal_starts_pending_and_blocked():
    proposal = emit_tooling_proposal(
        origin="ai_constraint_engine",
        actor="ai",
        intent="Suggest tooling validation improvement",
        change_type="tooling_change",
        target="afritech/afriprogramming/tooling_surfaces.py",
        diff='{"op":"add","path":"/x","value":"proposal"}',
    )
    payload = proposal.canonical_dict()

    assert payload["schema"] == PROPOSAL_SCHEMA
    assert payload["validation"]["status"] == "pending"
    assert payload["governance"]["status"] == "pending"
    assert payload["activation"]["status"] == "blocked"
    assert len(payload["proposal_hash"]) == 64
    assert evaluate_mutation_request(None)["mutation_allowed"] is False


def test_proposal_validation_blocks_protected_targets():
    proposal = emit_tooling_proposal(
        origin="ai_constraint_engine",
        actor="ai",
        intent="Unsafe governance mutation",
        change_type="tooling_change",
        target="afritech/governance/INDEX.yaml",
        diff='{"op":"replace","path":"/unsafe","value":true}',
    )
    validated = validate_proposal(proposal)

    assert validated.validation.status == "fail"
    assert "protected target mutation is forbidden" in validated.validation.violations


def test_governance_approval_requires_validation_and_explicit_signer():
    proposal = emit_tooling_proposal(
        origin="multi_agent_orchestrator",
        actor="system",
        intent="Governed validator update",
        change_type="validator_change",
        target="afritech/ci/example_validator.py",
        diff='{"op":"add","path":"/guard","value":"safe"}',
    )

    with pytest.raises(ToolingProposalError):
        approve_proposal(
            proposal,
            approved_by=("governance-council",),
            timestamp="2026-06-06T00:00:00Z",
            approval_ref="GOV-UNVALIDATED",
        )

    validated = validate_proposal(proposal)
    with pytest.raises(ToolingProposalError):
        approve_proposal(
            validated,
            approved_by=(),
            timestamp="2026-06-06T00:00:00Z",
            approval_ref="GOV-EMPTY",
        )

    approved = approve_proposal(
        validated,
        approved_by=("governance-council",),
        timestamp="2026-06-06T00:00:00Z",
        approval_ref="GOV-001",
    )
    rejected = reject_proposal(validated, approval_ref="GOV-REJECT")

    assert approved.governance.status == "approved"
    assert approved.governance.approved_by == ("governance-council",)
    assert rejected.governance.status == "rejected"


def test_activation_gate_requires_validation_and_governance_approval():
    proposal = emit_tooling_proposal(
        origin="afriprogramming_cli",
        actor="user",
        intent="Prepare CLI proposal command",
        change_type="tooling_change",
        target="afritech/afriprogramming/tooling_surfaces.py",
        diff='{"op":"add","path":"/commands/-","value":"afri propose"}',
    )

    with pytest.raises(ToolingProposalError):
        activation_gate(proposal, timestamp="2026-06-06T00:00:00Z")

    validated = validate_proposal(proposal)
    with pytest.raises(ToolingProposalError):
        activation_gate(validated, timestamp="2026-06-06T00:00:00Z")

    approved = approve_proposal(
        validated,
        approved_by=("governance-council",),
        timestamp="2026-06-06T00:00:00Z",
        approval_ref="GOV-001",
    )
    ready = activation_gate(approved, timestamp="2026-06-06T00:00:01Z")
    decision = evaluate_mutation_request(ready)

    assert ready.activation.status == "ready"
    assert ready.activation.execution_performed is False
    assert decision["mutation_allowed"] is False
    assert decision["requires_activation_layer"] is True


def test_proposal_governance_validators_pass_directly():
    tooling_proposal_emission_validator.validate_tooling_proposal_emission()
    governance_approval_flow_validator.validate_governance_approval_flow()
    tooling_activation_gate_validator.validate_tooling_activation_gate()


def test_proposal_governance_validator_cli_entrypoints_pass():
    for validator in VALIDATORS:
        result = subprocess.run(
            [sys.executable, "-m", validator.VALIDATOR_NAME],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASSED" in result.stdout
