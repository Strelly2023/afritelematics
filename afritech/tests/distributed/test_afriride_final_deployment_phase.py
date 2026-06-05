from __future__ import annotations

from pathlib import Path

from afritech.ci.afriride_final_deployment_phase_validator import validate


def test_final_deployment_phase_validator_passes():
    assert validate() is True


def test_readiness_matrix_keeps_live_activation_gated():
    text = Path("docs/pilot/AFRIRIDE_GA_ELITE_READINESS_MATRIX.md").read_text(
        encoding="utf-8"
    )

    assert "repo_side_ready = true" in text
    assert "live_pilot_authorized = false" in text
    assert "production_proven = false" in text


def test_activation_playbook_has_stop_conditions():
    text = Path("docs/pilot/AFRIRIDE_REAL_WORLD_ACTIVATION_PLAYBOOK.md").read_text(
        encoding="utf-8"
    )

    assert "Stop Conditions" in text
    assert "go_authorized = false" in text
    assert "signed event path fails" in text


def test_topology_preserves_authority_boundaries():
    text = Path("docs/pilot/AFRIRIDE_DEPLOYMENT_TOPOLOGY.md").read_text(
        encoding="utf-8"
    )

    assert "Mobile apps are interface-only" in text
    assert "Operator dashboard is observer-only" in text
    assert "Ledger and replay remain protocol-owned" in text


def test_risk_register_preserves_claim_discipline():
    text = Path("docs/pilot/AFRIRIDE_RISK_CONTROL_REGISTER.md").read_text(
        encoding="utf-8"
    )

    assert "controlled pilot" in text
    assert "production-proven" in text
    assert "guaranteed ride execution" in text
