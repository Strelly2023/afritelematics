from __future__ import annotations

from afritech.guards.guard_afroprog_workspace import validate


def test_afroprog_workspace_governance_chain_passes() -> None:
    report = validate()

    assert report.adr_id == "ADR-0021"
    assert report.rule_id == "RULE-041"
    assert report.workspace_mode == "codex_style"
    assert report.proposal_only is True
    assert report.governance_linked is True
