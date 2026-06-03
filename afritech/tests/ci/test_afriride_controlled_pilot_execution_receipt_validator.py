"""Tests for the AfriRide controlled pilot execution receipt validator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from afritech.ci.afriride_controlled_pilot_execution_receipt_validator import (
    AfriRideControlledPilotExecutionReceiptValidationError,
    validate_contract,
    validate_receipt,
)
from afritech.tests.ci.test_afriride_controlled_pilot_evidence_bundle_validator import (
    _build_valid_bundle,
    _read_json,
    _write_json,
)


def test_execution_receipt_contract_is_verified() -> None:
    report = validate_contract()

    assert report.verified is True
    assert report.classification == "proof_anchor"
    assert report.total_scenarios == 16
    assert report.introduces_new_truth is False


def test_valid_execution_receipt_is_accepted(tmp_path: Path) -> None:
    bundle_root = _build_valid_bundle(tmp_path)
    receipt_path = _write_valid_receipt(tmp_path, bundle_root)

    report = validate_receipt(receipt_path, bundle_root)

    assert report.verified is True
    assert report.receipt_id == "receipt-test"
    assert report.scenarios_executed == 16
    assert report.replay_success_rate == "100%"
    assert report.final_status == "ADMISSIBLE"


def test_receipt_rejects_mismatched_bundle_hash(tmp_path: Path) -> None:
    bundle_root = _build_valid_bundle(tmp_path)
    receipt_path = _write_valid_receipt(tmp_path, bundle_root)
    receipt = _read_json(receipt_path)
    receipt["evidence_bundle"]["bundle_hash"] = "different-hash"
    _write_json(receipt_path, receipt)

    with pytest.raises(
        AfriRideControlledPilotExecutionReceiptValidationError,
        match="mismatched bundle hash",
    ):
        validate_receipt(receipt_path, bundle_root)


def test_receipt_rejects_replay_less_than_100_percent(tmp_path: Path) -> None:
    bundle_root = _build_valid_bundle(tmp_path)
    receipt_path = _write_valid_receipt(tmp_path, bundle_root)
    receipt = _read_json(receipt_path)
    receipt["replay_verification"]["replay_success_rate"] = "99%"
    _write_json(receipt_path, receipt)

    with pytest.raises(
        AfriRideControlledPilotExecutionReceiptValidationError,
        match="Replay success less than 100|replay success less than 100",
    ):
        validate_receipt(receipt_path, bundle_root)


def test_receipt_rejects_scenario_count_less_than_16(tmp_path: Path) -> None:
    bundle_root = _build_valid_bundle(tmp_path)
    receipt_path = _write_valid_receipt(tmp_path, bundle_root)
    receipt = _read_json(receipt_path)
    receipt["pilot_scope"]["total_scenarios"] = 15
    _write_json(receipt_path, receipt)

    with pytest.raises(
        AfriRideControlledPilotExecutionReceiptValidationError,
        match="scenario count less than 16",
    ):
        validate_receipt(receipt_path, bundle_root)


def test_receipt_rejects_false_integrity_flag(tmp_path: Path) -> None:
    bundle_root = _build_valid_bundle(tmp_path)
    receipt_path = _write_valid_receipt(tmp_path, bundle_root)
    receipt = _read_json(receipt_path)
    receipt["integrity_checks"]["participant_registry_valid"] = False
    _write_json(receipt_path, receipt)

    with pytest.raises(
        AfriRideControlledPilotExecutionReceiptValidationError,
        match="integrity flag false",
    ):
        validate_receipt(receipt_path, bundle_root)


def test_receipt_rejects_missing_constraint_acknowledgement(tmp_path: Path) -> None:
    bundle_root = _build_valid_bundle(tmp_path)
    receipt_path = _write_valid_receipt(tmp_path, bundle_root)
    receipt = _read_json(receipt_path)
    receipt["constraints_acknowledged"]["not_market_ready"] = False
    _write_json(receipt_path, receipt)

    with pytest.raises(
        AfriRideControlledPilotExecutionReceiptValidationError,
        match="constraint flags missing",
    ):
        validate_receipt(receipt_path, bundle_root)


def _write_valid_receipt(tmp_path: Path, bundle_root: Path) -> Path:
    manifest = _read_json(bundle_root / "bundle_manifest.json")
    summary = _read_json(bundle_root / "pilot_completion_summary.json")
    receipt_path = tmp_path / "execution_receipt.json"
    receipt = {
        "receipt_id": "receipt-test",
        "generated_at": "2026-06-02T10:00:00+10:00",
        "evidence_origin": manifest["evidence_origin"],
        "pilot_scope": {
            "locations": ["Melbourne", "Bujumbura_Uvira", "Kinshasa"],
            "total_scenarios": 16,
        },
        "evidence_bundle": {
            "bundle_id": manifest["bundle_id"],
            "bundle_hash": manifest["hash"],
            "manifest_hash": manifest["hash"],
            "verified": True,
        },
        "execution_summary": {
            "scenarios_executed": summary["scenarios_executed"],
            "pass_count": summary["pass_count"],
            "fail_count": summary["fail_count"],
            "isolated_count": summary["isolated_count"],
        },
        "replay_verification": {
            "replay_success_rate": "100%",
            "all_hashes_match": True,
        },
        "integrity_checks": {
            "identity_integrity": True,
            "event_integrity": True,
            "participant_registry_valid": True,
            "device_registry_valid": True,
        },
        "incident_accountability": {
            "total_incidents": manifest["incident_count"],
            "all_recorded": True,
        },
        "final_status": "ADMISSIBLE",
        "constraints_acknowledged": {
            "not_production_ready": True,
            "not_scalable": True,
            "not_market_ready": True,
        },
    }
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt_path
