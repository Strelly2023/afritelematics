"""Tests for the final AfriRide Wave 6 closure triad validators."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from afritech.ci.afriride_controlled_pilot_certification_validator import (
    AfriRideControlledPilotCertificationValidationError,
    validate_certificate,
    validate_contract as validate_certification_contract,
)
from afritech.ci.afriride_controlled_pilot_evidence_automation_validator import (
    validate_contract as validate_automation_contract,
)
from afritech.ci.afriride_wave7_go_no_go_gate_validator import (
    validate_contract as validate_go_no_go_contract,
)
from afritech.tests.ci.test_afriride_controlled_pilot_evidence_bundle_validator import (
    _build_valid_bundle,
    _read_json,
    _write_json,
)
from afritech.tests.ci.test_afriride_controlled_pilot_execution_receipt_validator import (
    _write_valid_receipt,
)


def test_evidence_automation_contract_is_verified() -> None:
    report = validate_automation_contract()

    assert report.verified is True
    assert report.scenarios_required == 16
    assert report.manual_evidence_construction_allowed is False
    assert report.replay_verification_required is True


def test_controlled_pilot_certification_contract_is_verified() -> None:
    report = validate_certification_contract()

    assert report.verified is True
    assert report.required_scenarios == 16
    assert report.production_readiness_claimed is False


def test_wave7_go_no_go_gate_contract_is_verified() -> None:
    report = validate_go_no_go_contract()

    assert report.verified is True
    assert report.controlled_pilot_ready_to_run is True
    assert report.controlled_pilot_completion_claimed is False


def test_valid_controlled_pilot_certificate_is_accepted(tmp_path: Path) -> None:
    bundle_root = _build_valid_bundle(tmp_path)
    receipt_path = _write_valid_receipt(tmp_path, bundle_root)
    certificate_path = _write_valid_certificate(tmp_path, receipt_path, bundle_root)

    validate_certificate(certificate_path, receipt_path, bundle_root)


def test_certificate_rejects_production_readiness_claim(tmp_path: Path) -> None:
    bundle_root = _build_valid_bundle(tmp_path)
    receipt_path = _write_valid_receipt(tmp_path, bundle_root)
    certificate_path = _write_valid_certificate(tmp_path, receipt_path, bundle_root)
    certificate = _read_json(certificate_path)
    certificate["constraints"]["not_production_ready"] = False
    _write_json(certificate_path, certificate)

    with pytest.raises(
        AfriRideControlledPilotCertificationValidationError,
        match="constraint flag missing",
    ):
        validate_certificate(certificate_path, receipt_path, bundle_root)


def _write_valid_certificate(
    tmp_path: Path,
    receipt_path: Path,
    bundle_root: Path,
) -> Path:
    receipt = _read_json(receipt_path)
    manifest = _read_json(bundle_root / "bundle_manifest.json")
    certificate_path = tmp_path / "AFRIRIDE_CONTROLLED_PILOT_CERTIFICATE.json"
    certificate = {
        "certificate_id": "certificate-test",
        "generated_at": "2026-06-02T11:00:00+10:00",
        "evidence_origin": manifest["evidence_origin"],
        "execution_receipt": {
            "receipt_id": receipt["receipt_id"],
            "status": "VALID",
        },
        "evidence_bundle": {
            "bundle_id": manifest["bundle_id"],
            "validated": True,
        },
        "verification": {
            "validators_passed": True,
            "replay_consistent": True,
            "identity_integrity": True,
        },
        "scope": {
            "locations": 3,
            "scenarios": 16,
        },
        "classification": "CONTROLLED_PILOT_CERTIFIED",
        "constraints": {
            "not_production_ready": True,
            "not_scalable": True,
            "not_market_ready": True,
        },
    }
    certificate_path.write_text(
        json.dumps(certificate, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return certificate_path
