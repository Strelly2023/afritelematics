from __future__ import annotations

from afritech.guards.guard_runtime_boundary_governance import validate


def test_runtime_boundary_governance_chain_passes() -> None:
    report = validate()

    assert report.adr_id == "ADR-0022"
    assert report.rule_id == "RULE-042"
    assert report.bind_id == "BIND-021"
    assert report.validator_clean is True
    assert report.scan_current is True
    assert report.graph_current is True
    assert report.workflow_enforced is True
    assert report.optimization_active is True
