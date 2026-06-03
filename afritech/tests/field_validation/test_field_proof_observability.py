from __future__ import annotations

import pytest

from afriride.field_validation.proof_observability import (
    AUTHORITY_DISCLAIMER,
    FieldProofDashboard,
    ProofObservabilityError,
    build_field_proof_dashboard,
    write_field_proof_dashboard,
)
from afritech.ci.afriride_field_observability_validator import validate


def test_field_proof_dashboard_reports_all_proof_health_metrics():
    dashboard = build_field_proof_dashboard()
    payload = dashboard.canonical_dict()
    metrics = payload["metrics"]

    assert metrics["healthy"] is True
    assert metrics["replay_equivalence_rate"] == 1.0
    assert metrics["identity_equivalence_rate"] == 1.0
    assert metrics["pricing_equivalence_rate"] == 1.0
    assert metrics["admissibility_equivalence_rate"] == 1.0
    assert metrics["dispute_reproducibility_rate"] == 1.0
    assert metrics["drift_detection_count"] == 0
    assert payload["authority_disclaimer"] == AUTHORITY_DISCLAIMER


def test_field_observability_validator_accepts_dashboard():
    report = validate()

    assert report.verified is True
    assert len(report.dashboard_hash) == 64


def test_field_dashboard_report_is_reproducible(tmp_path):
    output = tmp_path / "proof_dashboard.json"
    first = write_field_proof_dashboard(output)
    second = build_field_proof_dashboard()

    assert first.dashboard_hash == second.dashboard_hash


def test_field_observability_cannot_claim_truth_authority():
    dashboard = build_field_proof_dashboard()

    with pytest.raises(ProofObservabilityError):
        FieldProofDashboard(
            afriride_field_hash=dashboard.afriride_field_hash,
            authority_disclaimer="Field dashboard defines truth.",
            metrics=dashboard.metrics,
            scenario_hashes=dashboard.scenario_hashes,
        )

