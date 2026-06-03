from __future__ import annotations

from pathlib import Path

import pytest

from afritech.ci.afriride_controlled_pilot_layer_validator import (
    AfriRideControlledPilotLayerValidationError,
    validate,
)


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/proof/AFRIRIDE_CONTROLLED_PILOT_LAYER.md"
)


def test_controlled_pilot_layer_contract_is_verified() -> None:
    report = validate()

    assert report.verified is True
    assert report.truth_authority == "replay_only"
    assert report.production_readiness_claimed is False
    assert report.pipeline[-1] == "registry_seal"


def test_controlled_pilot_layer_declares_non_goals() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "It is not a production ride-hailing system." in text
    assert "No production readiness claims" not in text
    assert "production_readiness_claimed: false" in text
    assert "external_runtime_guarantees_claimed: false" in text


def test_controlled_pilot_layer_requires_all_surfaces_implemented(tmp_path: Path) -> None:
    mutated = tmp_path / "pilot.md"
    mutated.write_text(
        DOC.read_text(encoding="utf-8").replace(
            "afritech.core.matching_engine: IMPLEMENTED",
            "afritech.core.matching_engine: PLANNED",
        ),
        encoding="utf-8",
    )

    with pytest.raises(AfriRideControlledPilotLayerValidationError):
        validate(mutated)


def test_controlled_pilot_layer_rejects_production_claim(tmp_path: Path) -> None:
    mutated = tmp_path / "pilot.md"
    mutated.write_text(
        DOC.read_text(encoding="utf-8").replace(
            "production_readiness_claimed: false",
            "production_readiness_claimed: true",
        ),
        encoding="utf-8",
    )

    with pytest.raises(AfriRideControlledPilotLayerValidationError):
        validate(mutated)
