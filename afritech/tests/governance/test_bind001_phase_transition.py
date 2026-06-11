from __future__ import annotations

from pathlib import Path

import yaml

from afritech.guards.guard_phase2_migration import validate


ROOT = Path(__file__).resolve().parents[3]
BIND = ROOT / "afritech/governance/bindings/BIND-001-phase1-phase2.yaml"
GATE = ROOT / "scripts/run_cutover_gate.sh"


def load_bind() -> dict:
    payload = yaml.safe_load(BIND.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_bind001_targets_resolve() -> None:
    bind = load_bind()

    assert bind["id"] == "BIND-001"
    assert len(bind["bindings"]) == 5

    for relative in (
        "docs/pilot/AFRIRIDE_PHASE1_SETUP_RUNBOOK.md",
        "docs/pilot/AFRIRIDE_PHASE2_MIGRATION_GOVERNANCE_SPEC.md",
        "docs/pilot/AFRIRIDE_PHASE3_LIVE_OPERATIONS_MONITORING_GOVERNANCE_SPEC.md",
        "scripts/run_cutover_gate.sh",
    ):
        assert (ROOT / relative).exists(), f"missing binding target: {relative}"


def test_bind001_execution_flow_and_rules_are_complete() -> None:
    bind = load_bind()

    assert tuple(step["binding"] for step in bind["execution_flow"]) == (
        "BIND-001-1",
        "BIND-001-2",
        "BIND-001-3",
        "BIND-001-4",
        "BIND-001-5",
    )
    for rule_id in (
        "RULE-001",
        "RULE-001-1",
        "RULE-001-2",
        "RULE-001-3",
        "RULE-001-4",
        "RULE-001-5",
    ):
        assert rule_id in bind["linked_rules"]


def test_phase2_guard_validates_binding_chain() -> None:
    report = validate()

    assert report.verified is True
    assert report.bind_id == "BIND-001"
    assert report.phase3_spec_present is True
    assert report.required_gate_count == 5


def test_cutover_gate_runner_wires_setup_guard_and_cutover_runbook() -> None:
    text = GATE.read_text(encoding="utf-8")

    for required in (
        "python3 -m afritech.guards.guard_phase1_runbook",
        "python3 -m afritech.guards.guard_phase2_migration",
        "scripts/run_phase1_setup.sh",
        "scripts/afriride_postgres_cutover_runbook.sh",
        "--skip-phase1",
        "--skip-guards",
        "GO: cutover gate passed",
        "NO-GO: cutover gate failed",
    ):
        assert required in text
