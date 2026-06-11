from __future__ import annotations

from pathlib import Path

import yaml

from afritech.guards.guard_phase1_runbook import validate


ROOT = Path(__file__).resolve().parents[3]
RULE = ROOT / "afritech/governance/rules/RULE-001-phase1-runbook.yaml"
SCRIPT = ROOT / "scripts/run_phase1_setup.sh"


def load_rule() -> dict:
    payload = yaml.safe_load(RULE.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_rule001_declares_phase1_governance_contract() -> None:
    rule = load_rule()

    assert rule["id"] == "RULE-001"
    assert rule["status"] == "ACTIVE"
    assert rule["classification"] == "OPERATOR_SETUP_GOVERNANCE_RULE"

    linked = rule["linked_artifacts"]
    assert linked["runbook_doc"] == "docs/pilot/AFRIRIDE_PHASE1_SETUP_RUNBOOK.md"
    assert linked["guard"] == "afritech/guards/guard_phase1_runbook.py"
    assert linked["runner"] == "scripts/run_phase1_setup.sh"
    assert linked["phase2_spec"] == "docs/pilot/AFRIRIDE_PHASE2_MIGRATION_GOVERNANCE_SPEC.md"


def test_rule001_captures_real_code_alignment_and_phase2_gate() -> None:
    rule = load_rule()
    contract = rule["contract"]

    assert contract["code_alignment"]["default_sqlite_path"] == "afriride_system/pilot_state.sqlite3"
    assert contract["code_alignment"]["required_http_surfaces"] == [
        "/health",
        "/docs",
        "/auth/token",
        "/passenger/request-ride",
    ]
    assert "AFRIRIDE_DATABASE_URL" in contract["setup_contract"]["required_env_vars"]
    assert "AFRIRIDE_PHASE2_MIGRATION_GOVERNANCE_SPEC.md" in contract["phase2_gate"]["required_forward_links"]


def test_phase1_guard_validates_governance_chain() -> None:
    report = validate()

    assert report.verified is True
    assert report.rule_id == "RULE-001"
    assert report.sqlite_path == "afriride_system/pilot_state.sqlite3"
    assert report.phase2_spec_present is True


def test_phase1_setup_runner_exposes_guarded_execution_modes() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    for required in (
        "python3 -m afritech.guards.guard_phase1_runbook",
        "--install-deps",
        "--with-postgres",
        "--boot-api",
        "curl -sS",
        "uvicorn afriride_system.api.main:app",
        "/health",
        "/auth/token",
        "/passenger/request-ride",
        "AFRIRIDE_DATABASE_URL",
    ):
        assert required in text
