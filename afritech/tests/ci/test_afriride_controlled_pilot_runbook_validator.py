from __future__ import annotations

from pathlib import Path

import pytest

from afritech.ci.afriride_controlled_pilot_runbook_validator import (
    AfriRideControlledPilotRunbookValidationError,
    validate,
)


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/proof/AFRIRIDE_CONTROLLED_PILOT_RUNBOOK.md"
)


def test_controlled_pilot_runbook_is_verified() -> None:
    report = validate()

    assert report.verified is True
    assert report.artifact_type == "execution_contract"
    assert report.scenario_count == 19
    assert report.production_launch_claimed is False


def test_controlled_pilot_runbook_declares_hard_execution_rules() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "ABORT RUN (hard stop)" in text
    assert "NO incident = no admissibility" in text
    assert "Execution Hash == Replay Hash" in text
    assert "Event -> Execution -> Replay -> Proof" in text


def test_controlled_pilot_runbook_rejects_scenario_reordering(tmp_path: Path) -> None:
    mutated = tmp_path / "runbook.md"
    mutated.write_text(
        DOC.read_text(encoding="utf-8").replace(
            "      - A1\n      - A2\n",
            "      - A2\n      - A1\n",
        ),
        encoding="utf-8",
    )

    with pytest.raises(AfriRideControlledPilotRunbookValidationError):
        validate(mutated)


def test_controlled_pilot_runbook_rejects_production_claim(tmp_path: Path) -> None:
    mutated = tmp_path / "runbook.md"
    mutated.write_text(
        DOC.read_text(encoding="utf-8").replace(
            "production_launch_claimed: false",
            "production_launch_claimed: true",
        ),
        encoding="utf-8",
    )

    with pytest.raises(AfriRideControlledPilotRunbookValidationError):
        validate(mutated)
