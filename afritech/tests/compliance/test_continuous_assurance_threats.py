from __future__ import annotations

import json
from pathlib import Path

import pytest

from afritech.compliance.continuous_assurance import run_continuous_assurance_cycle
from afritech.compliance.continuous_assurance_threats import (
    THREAT_SCENARIOS,
    ContinuousAssuranceThreatError,
    simulate_continuous_assurance_threats,
    validate_continuous_assurance_threats,
)


def _make_evidence_files(tmp_path: Path) -> list[Path]:
    paths: list[Path] = []
    for name in ("crypto.pdf", "pentest.pdf", "provider.txt", "incident.md"):
        path = tmp_path / name
        path.write_text(f"evidence:{name}", encoding="utf-8")
        paths.append(path)
    return paths


@pytest.mark.django_db
def test_threat_simulation_detects_all_scenarios_and_live_ai_alerts(tmp_path: Path) -> None:
    package = run_continuous_assurance_cycle(
        evidence_items=_make_evidence_files(tmp_path),
        payment_reference="threat.simulation.001",
    )

    report = validate_continuous_assurance_threats(package)

    assert report.verified is True
    assert report.trust_score == 1.0
    assert [result.scenario_id for result in report.scenario_results] == [
        scenario.scenario_id for scenario in THREAT_SCENARIOS
    ]
    assert all(result.detected for result in report.scenario_results)
    assert all(result.anomaly_alerts for result in report.scenario_results)
    assert all(result.ai_result["anomaly"] is True for result in report.scenario_results)
    assert set(report.live_ai_risks).issubset({"HIGH", "CRITICAL"})


@pytest.mark.django_db
def test_threat_simulation_is_deterministic(tmp_path: Path) -> None:
    package = run_continuous_assurance_cycle(
        evidence_items=_make_evidence_files(tmp_path),
        payment_reference="threat.simulation.002",
    )

    first = simulate_continuous_assurance_threats(package)
    second = simulate_continuous_assurance_threats(package)

    assert first.report_hash() == second.report_hash()
    assert first.canonical_dict() == second.canonical_dict()


@pytest.mark.django_db
def test_threat_simulation_serialization_roundtrip(tmp_path: Path) -> None:
    package = run_continuous_assurance_cycle(
        evidence_items=_make_evidence_files(tmp_path),
        payment_reference="threat.simulation.003",
    )

    report = simulate_continuous_assurance_threats(package)
    encoded = json.dumps(report.canonical_dict(), sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded["verified"] is True
    assert decoded["trust_score"] == 1.0
    assert decoded["scenario_results"][0]["invariant_report"]["package_hash"] == package.package_hash


@pytest.mark.django_db
def test_threat_simulation_rejects_invalid_baseline() -> None:
    package = run_continuous_assurance_cycle(
        evidence_items=[],
        payment_reference="threat.simulation.empty",
    )

    with pytest.raises(ContinuousAssuranceThreatError, match="IA-006:.*IA-007:"):
        validate_continuous_assurance_threats(package)
