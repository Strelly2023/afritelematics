from __future__ import annotations

from afritech.ci.classification_ci_validator import (
    resolve_signals,
    run_classification_ci_validation,
    _enforce_rules,
)
from afritech.ci.afritech_check_classification_status import (
    ClassificationEngine,
    SystemSignals,
)


def test_classification_ci_passes_and_preserves_truth_boundary():
    result = run_classification_ci_validation()

    assert result["state"] == "CONTROLLED_PILOT_READY_SYSTEM"
    assert result["truth_boundary"]["live_pilot_authorized"] is False
    assert result["truth_boundary"]["production_proven"] is False


def test_classification_signals_are_repo_resolved():
    signals = resolve_signals()

    assert signals.constitutional_pass is True
    assert signals.consensus_valid is True
    assert signals.controlled_pilot_prepared is True
    assert signals.live_pilot_authorized is False
    assert signals.production_proven is False


def test_classification_ci_blocks_live_pilot_authorization():
    signals = SystemSignals(
        constitutional_pass=True,
        replay_valid=True,
        proof_surface_valid=True,
        consensus_valid=True,
        hardening_implemented=True,
        adversarial_implemented=True,
        multi_domain_validation=True,
        observability_ready=True,
        deployment_control_ready=True,
        app_surface_ready=True,
        controlled_pilot_prepared=True,
        live_pilot_authorized=True,
        production_proven=False,
    )
    result = ClassificationEngine(signals).classify()

    try:
        _enforce_rules(result)
    except RuntimeError as exc:
        assert "live_pilot_authorized=True" in str(exc)
    else:
        raise AssertionError("classification CI did not block live pilot")


def test_classification_ci_blocks_production_proven():
    signals = SystemSignals(
        constitutional_pass=True,
        replay_valid=True,
        proof_surface_valid=True,
        consensus_valid=True,
        hardening_implemented=True,
        adversarial_implemented=True,
        multi_domain_validation=True,
        observability_ready=True,
        deployment_control_ready=True,
        app_surface_ready=True,
        controlled_pilot_prepared=True,
        live_pilot_authorized=True,
        production_proven=True,
    )
    result = ClassificationEngine(signals).classify()

    try:
        _enforce_rules(result)
    except RuntimeError as exc:
        assert "production_proven=True" in str(exc)
    else:
        raise AssertionError("classification CI did not block production claim")
