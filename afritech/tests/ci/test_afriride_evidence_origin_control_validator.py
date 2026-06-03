"""Tests for AfriRide evidence origin control."""

from __future__ import annotations

from pathlib import Path

import pytest

from afritech.ci.afriride_evidence_origin_control_validator import (
    AfriRideEvidenceOriginControlValidationError,
    validate_bundle_origin,
    validate_contract,
)
from afritech.tests.ci.test_afriride_controlled_pilot_evidence_bundle_validator import (
    _build_valid_bundle,
    _read_json,
    _seal_manifest,
    _write_json,
)


def test_evidence_origin_control_contract_is_verified() -> None:
    report = validate_contract()

    assert report.verified is True
    assert report.certification_required_origin == "field_observed"
    assert report.wave7_required_origin == "field_observed"


def test_field_observed_bundle_is_allowed_for_certification(tmp_path: Path) -> None:
    bundle_root = _build_valid_bundle(tmp_path)

    origin = validate_bundle_origin(bundle_root, require_field_observed=True)

    assert origin == "field_observed"


def test_synthetic_bundle_is_valid_structurally_but_blocked_for_certification(
    tmp_path: Path,
) -> None:
    bundle_root = _build_valid_bundle(tmp_path)
    _set_origin(bundle_root, "synthetic")

    origin = validate_bundle_origin(bundle_root, require_field_observed=False)

    assert origin == "synthetic"
    with pytest.raises(
        AfriRideEvidenceOriginControlValidationError,
        match="not admissible for certification",
    ):
        validate_bundle_origin(bundle_root, require_field_observed=True)


def test_origin_mismatch_rejects_bundle(tmp_path: Path) -> None:
    bundle_root = _build_valid_bundle(tmp_path)
    metadata = _read_json(bundle_root / "bundle_metadata.json")
    metadata["evidence_origin"] = "synthetic"
    _write_json(bundle_root / "bundle_metadata.json", metadata)
    _seal_manifest(bundle_root)

    with pytest.raises(RuntimeError, match="evidence origin mismatch"):
        validate_bundle_origin(bundle_root, require_field_observed=False)


def _set_origin(bundle_root: Path, origin: str) -> None:
    metadata = _read_json(bundle_root / "bundle_metadata.json")
    manifest = _read_json(bundle_root / "bundle_manifest.json")
    metadata["evidence_origin"] = origin
    manifest["evidence_origin"] = origin
    _write_json(bundle_root / "bundle_metadata.json", metadata)
    _write_json(bundle_root / "bundle_manifest.json", manifest)
    _seal_manifest(bundle_root)
