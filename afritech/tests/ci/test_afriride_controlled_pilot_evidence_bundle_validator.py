"""Tests for the AfriRide controlled pilot evidence bundle validator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from afritech.ci.afriride_controlled_pilot_evidence_bundle_validator import (
    ALL_SCENARIO_IDS,
    REQUIRED_LOCATIONS,
    SCENARIO_IDS,
    AfriRideControlledPilotEvidenceBundleValidationError,
    compute_bundle_hash,
    validate_bundle,
    validate_contract,
)


def test_evidence_bundle_contract_is_verified() -> None:
    report = validate_contract()

    assert report.verified is True
    assert report.scenarios_total == 16
    assert report.truth_authority == "replay_receipts"
    assert report.production_readiness_claimed is False


def test_valid_evidence_bundle_is_accepted(tmp_path: Path) -> None:
    bundle_root = _build_valid_bundle(tmp_path)

    report = validate_bundle(bundle_root)

    assert report.verified is True
    assert report.total_scenarios == 16
    assert report.receipts_count == 16
    assert report.replay_verified is True
    assert report.final_status == "ADMISSIBLE"


def test_replay_mismatch_rejects_bundle(tmp_path: Path) -> None:
    bundle_root = _build_valid_bundle(tmp_path)
    replay_path = bundle_root / "replay_verification_receipts" / "A1.json"
    replay = _read_json(replay_path)
    replay["replay_hash"] = "different-hash"
    _write_json(replay_path, replay)
    _seal_manifest(bundle_root)

    with pytest.raises(
        AfriRideControlledPilotEvidenceBundleValidationError,
        match="replay mismatch",
    ):
        validate_bundle(bundle_root)


def test_unregistered_participant_rejects_bundle(tmp_path: Path) -> None:
    bundle_root = _build_valid_bundle(tmp_path)
    receipt_path = (
        bundle_root
        / "scenario_execution_receipts"
        / "Kinshasa"
        / "E2"
        / "receipt.json"
    )
    receipt = _read_json(receipt_path)
    receipt["participants"]["driver"] = "driver-unregistered"
    _write_json(receipt_path, receipt)
    _seal_manifest(bundle_root)

    with pytest.raises(
        AfriRideControlledPilotEvidenceBundleValidationError,
        match="unregistered driver",
    ):
        validate_bundle(bundle_root)


def test_missing_incident_record_rejects_failed_scenario(tmp_path: Path) -> None:
    bundle_root = _build_valid_bundle(tmp_path)
    receipt_path = (
        bundle_root
        / "scenario_execution_receipts"
        / "Bujumbura_Uvira"
        / "D1"
        / "receipt.json"
    )
    receipt = _read_json(receipt_path)
    receipt["status"] = "FAIL"
    _write_json(receipt_path, receipt)
    summary_path = bundle_root / "pilot_completion_summary.json"
    summary = _read_json(summary_path)
    summary["pass_count"] = 15
    summary["fail_count"] = 1
    _write_json(summary_path, summary)
    _seal_manifest(bundle_root)

    with pytest.raises(
        AfriRideControlledPilotEvidenceBundleValidationError,
        match="missing incident record",
    ):
        validate_bundle(bundle_root)


def test_manifest_hash_mismatch_rejects_bundle(tmp_path: Path) -> None:
    bundle_root = _build_valid_bundle(tmp_path)
    manifest_path = bundle_root / "bundle_manifest.json"
    manifest = _read_json(manifest_path)
    manifest["hash"] = "invalid"
    _write_json(manifest_path, manifest)

    with pytest.raises(
        AfriRideControlledPilotEvidenceBundleValidationError,
        match="manifest hash invalid",
    ):
        validate_bundle(bundle_root)


def _build_valid_bundle(tmp_path: Path) -> Path:
    bundle_root = tmp_path / "pilot_evidence_bundle"
    (bundle_root / "scenario_execution_receipts").mkdir(parents=True)
    (bundle_root / "incident_records").mkdir()
    (bundle_root / "replay_verification_receipts").mkdir()

    _write_json(
        bundle_root / "bundle_metadata.json",
        {
            "bundle_id": "bundle-test",
            "evidence_origin": "field_observed",
        },
    )
    _write_json(
        bundle_root / "participant_registry.json",
        {
            "riders": [{"rider_id": "rider-001", "location": "Melbourne"}],
            "drivers": [
                {
                    "driver_id": "driver-001",
                    "vehicle": "Toyota Axio",
                    "location": "Kinshasa",
                }
            ],
        },
    )
    _write_json(
        bundle_root / "device_registry.json",
        {
            "devices": [
                {
                    "device_id": "device-rider-001",
                    "user_id": "rider-001",
                    "type": "rider",
                    "gps_enabled": True,
                    "network_type": "4G",
                },
                {
                    "device_id": "device-driver-001",
                    "user_id": "driver-001",
                    "type": "driver",
                    "gps_enabled": True,
                    "network_type": "unstable",
                },
            ]
        },
    )

    for location in REQUIRED_LOCATIONS:
        location_dir = bundle_root / "scenario_execution_receipts" / location
        location_dir.mkdir()
        for scenario_id in SCENARIO_IDS[location]:
            execution_hash = f"hash-{scenario_id.lower()}"
            scenario_dir = location_dir / scenario_id
            scenario_dir.mkdir()
            _write_json(
                scenario_dir / "receipt.json",
                {
                    "scenario_id": scenario_id,
                    "location": location,
                    "trip_id": f"trip-{scenario_id.lower()}",
                    "participants": {
                        "rider": "rider-001",
                        "driver": "driver-001",
                    },
                    "execution_hash": execution_hash,
                    "timestamp": "2026-06-02T09:00:00+10:00",
                    "status": "PASS",
                },
            )

    for scenario_id in ALL_SCENARIO_IDS:
        execution_hash = f"hash-{scenario_id.lower()}"
        _write_json(
            bundle_root / "replay_verification_receipts" / f"{scenario_id}.json",
            {
                "scenario_id": scenario_id,
                "execution_hash": execution_hash,
                "replay_hash": execution_hash,
                "match": True,
                "validator_status": "PASS",
            },
        )

    _write_json(
        bundle_root / "pilot_completion_summary.json",
        {
            "locations": list(REQUIRED_LOCATIONS),
            "scenarios_total": 16,
            "scenarios_executed": 16,
            "pass_count": 16,
            "fail_count": 0,
            "isolated_count": 0,
            "replay_success_rate": "100%",
            "identity_integrity": True,
            "event_integrity": True,
            "final_status": "ADMISSIBLE",
        },
    )
    _write_json(
        bundle_root / "bundle_manifest.json",
        {
            "bundle_id": "bundle-test",
            "generated_at": "2026-06-02T09:00:00+10:00",
            "evidence_origin": "field_observed",
            "locations_covered": 3,
            "total_scenarios": 16,
            "receipts_count": 16,
            "incident_count": 0,
            "replay_verified": True,
            "hash": "",
        },
    )
    _seal_manifest(bundle_root)
    return bundle_root


def _seal_manifest(bundle_root: Path) -> None:
    manifest_path = bundle_root / "bundle_manifest.json"
    manifest = _read_json(manifest_path)
    manifest["hash"] = compute_bundle_hash(bundle_root)
    _write_json(manifest_path, manifest)


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
