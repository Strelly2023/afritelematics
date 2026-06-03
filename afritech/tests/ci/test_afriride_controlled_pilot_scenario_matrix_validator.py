from __future__ import annotations

from pathlib import Path

import pytest

from afritech.ci.afriride_controlled_pilot_scenario_matrix_validator import (
    AfriRideControlledPilotScenarioMatrixValidationError,
    validate,
)


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/proof/AFRIRIDE_CONTROLLED_PILOT_SCENARIO_MATRIX.md"
)


def test_controlled_pilot_scenario_matrix_is_verified() -> None:
    report = validate()

    assert report.verified is True
    assert report.location_count == 3
    assert report.scenario_count == 16
    assert report.truth_authority == "replay_only"
    assert report.production_launch_claimed is False


def test_controlled_pilot_scenario_matrix_declares_global_law() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "System validity = survives ALL three environments" in text
    assert "A pilot system is considered valid ONLY IF" in text
    assert "production_launch_claimed: false" in text
    assert "operational_success_claimed: false" in text


def test_controlled_pilot_scenario_matrix_rejects_missing_location(tmp_path: Path) -> None:
    mutated = tmp_path / "matrix.md"
    mutated.write_text(
        DOC.read_text(encoding="utf-8").replace("    kinshasa:\n", "    kinshasa_removed:\n"),
        encoding="utf-8",
    )

    with pytest.raises(AfriRideControlledPilotScenarioMatrixValidationError):
        validate(mutated)


def test_controlled_pilot_scenario_matrix_rejects_production_claim(tmp_path: Path) -> None:
    mutated = tmp_path / "matrix.md"
    mutated.write_text(
        DOC.read_text(encoding="utf-8").replace(
            "production_launch_claimed: false",
            "production_launch_claimed: true",
        ),
        encoding="utf-8",
    )

    with pytest.raises(AfriRideControlledPilotScenarioMatrixValidationError):
        validate(mutated)
