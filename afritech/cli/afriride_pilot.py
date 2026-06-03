"""AfriRide controlled pilot evidence automation CLI."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from afritech.ci.afriride_controlled_pilot_certification_validator import (
    validate_certificate,
)
from afritech.ci.afriride_controlled_pilot_evidence_bundle_validator import (
    ALL_SCENARIO_IDS,
    REQUIRED_LOCATIONS,
    SCENARIO_IDS,
    compute_bundle_hash,
    validate_bundle,
)
from afritech.ci.afriride_controlled_pilot_execution_receipt_validator import (
    validate_receipt,
)
from afritech.ci.afriride_evidence_origin_control_validator import (
    validate_bundle_origin,
)


DEFAULT_GENERATED_AT = "2026-06-02T00:32:00+10:00"
SAMPLE_BUNDLE_ID = "AFRI-PILOT-W6-EXEC-001"
SAMPLE_RECEIPT_ID = "AFRI-EXEC-REC-W6-001"
SAMPLE_CERTIFICATE_ID = "AFRI-CERT-W6-001"


def build_sample_bundle(output: Path) -> Path:
    """Build a validator-compatible synthetic evidence bundle."""

    bundle_root = output
    _ensure_empty_bundle_dirs(bundle_root)

    _write_json(
        bundle_root / "bundle_metadata.json",
        {
            "bundle_id": SAMPLE_BUNDLE_ID,
            "evidence_origin": "synthetic",
            "generated_by": "afritech.cli.afriride_pilot",
        },
    )
    _write_json(
        bundle_root / "participant_registry.json",
        {
            "generated_at": DEFAULT_GENERATED_AT,
            "riders": [
                {"rider_id": "R-001", "location": "Melbourne"},
                {"rider_id": "R-002", "location": "Bujumbura_Uvira"},
                {"rider_id": "R-003", "location": "Kinshasa"},
            ],
            "drivers": [
                {"driver_id": "D-001", "vehicle": "Toyota Camry", "location": "Melbourne"},
                {"driver_id": "D-002", "vehicle": "Toyota Hiace", "location": "Bujumbura_Uvira"},
                {"driver_id": "D-003", "vehicle": "Suzuki Escudo", "location": "Kinshasa"},
            ],
        },
    )
    _write_json(
        bundle_root / "device_registry.json",
        {
            "devices": [
                {
                    "device_id": "DEV-R001",
                    "user_id": "R-001",
                    "type": "rider",
                    "gps_enabled": True,
                    "network_type": "4G",
                },
                {
                    "device_id": "DEV-D001",
                    "user_id": "D-001",
                    "type": "driver",
                    "gps_enabled": True,
                    "network_type": "stable",
                },
                {
                    "device_id": "DEV-D002",
                    "user_id": "D-002",
                    "type": "driver",
                    "gps_enabled": True,
                    "network_type": "offline_intermittent",
                },
                {
                    "device_id": "DEV-D003",
                    "user_id": "D-003",
                    "type": "driver",
                    "gps_enabled": True,
                    "network_type": "variable",
                },
            ]
        },
    )

    event_hashes: dict[str, str] = {}
    for location in REQUIRED_LOCATIONS:
        for scenario_id in SCENARIO_IDS[location]:
            events = _scenario_events(location, scenario_id)
            execution_hash = _hash_payload(events)
            event_hashes[scenario_id] = execution_hash
            _write_json(bundle_root / "event_logs" / f"{scenario_id}.json", {"events": events})
            _write_json(
                bundle_root / "replay_outputs" / f"{scenario_id}.json",
                {
                    "scenario_id": scenario_id,
                    "events": [event["type"] for event in events],
                    "replay_hash": execution_hash,
                    "deterministic": True,
                },
            )
            _write_scenario_receipt(
                bundle_root=bundle_root,
                location=location,
                scenario_id=scenario_id,
                execution_hash=execution_hash,
            )
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
        bundle_root / "global_validation_results.json",
        {
            "G1": {"replay_integrity": "PASS", "replay_success_rate": "100%"},
            "G2": {"identity_drift": 0, "identity_collisions": 0, "status": "PASS"},
            "G3": {"event_completeness": "100%", "missing_events": 0, "status": "PASS"},
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
            "bundle_id": SAMPLE_BUNDLE_ID,
            "generated_at": DEFAULT_GENERATED_AT,
            "evidence_origin": "synthetic",
            "locations_covered": 3,
            "total_scenarios": 16,
            "receipts_count": 16,
            "incident_count": 0,
            "replay_verified": True,
            "hash": "",
        },
    )
    _seal_manifest(bundle_root)
    validate_bundle(bundle_root)
    return bundle_root


def generate_execution_receipt(bundle_root: Path, output: Path) -> Path:
    """Generate a receipt derived from a validated evidence bundle."""

    validate_bundle(bundle_root)
    manifest = _read_json(bundle_root / "bundle_manifest.json")
    summary = _read_json(bundle_root / "pilot_completion_summary.json")
    evidence_origin = manifest["evidence_origin"]
    receipt = {
        "receipt_id": SAMPLE_RECEIPT_ID,
        "generated_at": DEFAULT_GENERATED_AT,
        "evidence_origin": evidence_origin,
        "pilot_scope": {
            "locations": list(REQUIRED_LOCATIONS),
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
            "replay_success_rate": summary["replay_success_rate"],
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
    _write_json(output, receipt)
    validate_receipt(output, bundle_root)
    return output


def generate_certificate(bundle_root: Path, receipt_path: Path, output: Path) -> Path:
    """Generate a controlled pilot certificate from a validated receipt."""

    validate_bundle_origin(bundle_root, require_field_observed=True)
    receipt_report = validate_receipt(receipt_path, bundle_root)
    bundle_report = validate_bundle(bundle_root)
    manifest = _read_json(bundle_root / "bundle_manifest.json")
    certificate = {
        "certificate_id": SAMPLE_CERTIFICATE_ID,
        "generated_at": DEFAULT_GENERATED_AT,
        "evidence_origin": manifest["evidence_origin"],
        "execution_receipt": {
            "receipt_id": receipt_report.receipt_id,
            "status": "VALID",
        },
        "evidence_bundle": {
            "bundle_id": bundle_report.bundle_id,
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
    _write_json(output, certificate)
    validate_certificate(output, receipt_path, bundle_root)
    return output


def _ensure_empty_bundle_dirs(bundle_root: Path) -> None:
    bundle_root.mkdir(parents=True, exist_ok=True)
    for rel_path in (
        "event_logs",
        "replay_outputs",
        "scenario_execution_receipts",
        "incident_records",
        "replay_verification_receipts",
    ):
        (bundle_root / rel_path).mkdir(parents=True, exist_ok=True)
    for location in REQUIRED_LOCATIONS:
        (bundle_root / "scenario_execution_receipts" / location).mkdir(
            parents=True,
            exist_ok=True,
        )


def _scenario_events(location: str, scenario_id: str) -> list[dict[str, Any]]:
    rider = {"Melbourne": "R-001", "Bujumbura_Uvira": "R-002", "Kinshasa": "R-003"}[location]
    driver = {"Melbourne": "D-001", "Bujumbura_Uvira": "D-002", "Kinshasa": "D-003"}[location]
    trip_id = f"T-{scenario_id}"
    base = [
        _event(scenario_id, 1, "REQUEST", trip_id, rider_id=rider),
        _event(scenario_id, 2, "MATCH", trip_id, driver_id=driver),
    ]
    variants: dict[str, list[dict[str, Any]]] = {
        "A1": base + [_event(scenario_id, 3, "ACCEPT", trip_id, driver_id=driver), _event(scenario_id, 4, "START", trip_id), _event(scenario_id, 5, "END", trip_id)],
        "A2": base + [_event(scenario_id, 3, "REJECT", trip_id, driver_id="D-MEL-R1"), _event(scenario_id, 4, "REJECT", trip_id, driver_id="D-MEL-R2"), _event(scenario_id, 5, "ACCEPT", trip_id, driver_id=driver), _event(scenario_id, 6, "START", trip_id), _event(scenario_id, 7, "END", trip_id)],
        "A3": [_event(scenario_id, 1, "REQUEST", trip_id, rider_id=rider), _event(scenario_id, 2, "CANCEL", trip_id, rider_id=rider)],
        "A4": base + [_event(scenario_id, 3, "TIMEOUT", trip_id, driver_id="D-MEL-T1"), _event(scenario_id, 4, "REASSIGN", trip_id, driver_id=driver), _event(scenario_id, 5, "ACCEPT", trip_id, driver_id=driver), _event(scenario_id, 6, "START", trip_id), _event(scenario_id, 7, "END", trip_id)],
        "A5": base + [_event(scenario_id, 3, "ACCEPT", trip_id, driver_id=driver), _event(scenario_id, 4, "START", trip_id), _event(scenario_id, 5, "END", trip_id), _event(scenario_id, 6, "PAYMENT_FAILED", trip_id)],
        "C1": base + [_event(scenario_id, 3, "ACCEPT", trip_id, driver_id=driver), _event(scenario_id, 4, "START", trip_id), _event(scenario_id, 5, "CROSS_BORDER_LOCATION", trip_id), _event(scenario_id, 6, "END", trip_id)],
        "C2": base + [_event(scenario_id, 3, "START", trip_id), _event(scenario_id, 4, "BUFFERED_GPS", trip_id), _event(scenario_id, 5, "FLUSH", trip_id), _event(scenario_id, 6, "END", trip_id)],
        "C3": base + [_event(scenario_id, 3, "EVENT_1", trip_id), _event(scenario_id, 5, "EVENT_3", trip_id), _event(scenario_id, 4, "EVENT_2_DELAYED", trip_id, ingested_offset=10), _event(scenario_id, 6, "END", trip_id)],
        "D1": base + [_event(scenario_id, 3, "START", trip_id), _event(scenario_id, 4, "GPS_ANOMALY", trip_id), _event(scenario_id, 5, "END", trip_id)],
        "D2": base + [_event(scenario_id, 3, "START", trip_id), _event(scenario_id, 4, "END", trip_id), _event(scenario_id, 5, "RIDER_CLAIM_PAID", trip_id, rider_id=rider), _event(scenario_id, 6, "DRIVER_CLAIM_UNPAID", trip_id, driver_id=driver)],
        "E1": base + [_event(scenario_id, 3, "PARTITION_ASSIGN", trip_id), _event(scenario_id, 4, "ACCEPT", trip_id, driver_id=driver), _event(scenario_id, 5, "START", trip_id), _event(scenario_id, 6, "END", trip_id)],
        "E2": base + [_event(scenario_id, 3, "ACCEPT_ATTEMPT", trip_id, driver_id="D-KIN-A"), _event(scenario_id, 4, "ACCEPT_ATTEMPT", trip_id, driver_id="D-KIN-B"), _event(scenario_id, 5, "ACCEPT", trip_id, driver_id=driver), _event(scenario_id, 6, "REJECT", trip_id, driver_id="D-KIN-B"), _event(scenario_id, 7, "END", trip_id)],
        "E3": base + [_event(scenario_id, 3, "START", trip_id), _event(scenario_id, 4, "ROUTE_DEVIATION", trip_id), _event(scenario_id, 5, "END", trip_id)],
        "F1": base + [_event(scenario_id, 3, "ACCEPT", trip_id, driver_id=driver), _event(scenario_id, 4, "INVALID_COMPLETE_ATTEMPT", trip_id, driver_id=driver), _event(scenario_id, 5, "VIOLATION", trip_id)],
        "F2": [_event(scenario_id, index, "REQUEST_BURST", f"{trip_id}-{index}", rider_id=rider) for index in range(1, 9)] + [_event(scenario_id, 9, "RATE_LIMIT_DECISION", trip_id)],
        "F3": base + [_event(scenario_id, 3, "ONLINE", trip_id, driver_id=driver), _event(scenario_id, 4, "OFFLINE", trip_id, driver_id=driver), _event(scenario_id, 5, "ONLINE", trip_id, driver_id=driver), _event(scenario_id, 6, "MATCH_DECISION", trip_id)],
    }
    return sorted(variants[scenario_id], key=lambda event: event["sequence_number"])


def _event(
    scenario_id: str,
    sequence: int,
    event_type: str,
    trip_id: str,
    *,
    rider_id: str | None = None,
    driver_id: str | None = None,
    ingested_offset: int = 0,
) -> dict[str, Any]:
    timestamp_minute = sequence
    payload: dict[str, Any] = {
        "event_id": f"EV-{scenario_id}-{sequence:03d}",
        "scenario_id": scenario_id,
        "sequence_number": sequence,
        "type": event_type,
        "trip_id": trip_id,
        "timestamp": f"2026-06-01T18:{timestamp_minute:02d}:00Z",
        "ingested_at": f"2026-06-01T18:{timestamp_minute + ingested_offset:02d}:05Z",
    }
    if rider_id:
        payload["rider_id"] = rider_id
    if driver_id:
        payload["driver_id"] = driver_id
    return payload


def _write_scenario_receipt(
    *,
    bundle_root: Path,
    location: str,
    scenario_id: str,
    execution_hash: str,
) -> None:
    receipt_dir = bundle_root / "scenario_execution_receipts" / location / scenario_id
    receipt_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        receipt_dir / "receipt.json",
        {
            "scenario_id": scenario_id,
            "location": location,
            "trip_id": f"T-{scenario_id}",
            "participants": {
                "rider": {"Melbourne": "R-001", "Bujumbura_Uvira": "R-002", "Kinshasa": "R-003"}[location],
                "driver": {"Melbourne": "D-001", "Bujumbura_Uvira": "D-002", "Kinshasa": "D-003"}[location],
            },
            "execution_hash": execution_hash,
            "timestamp": DEFAULT_GENERATED_AT,
            "status": "PASS",
        },
    )


def _seal_manifest(bundle_root: Path) -> None:
    manifest_path = bundle_root / "bundle_manifest.json"
    manifest = _read_json(manifest_path)
    manifest["hash"] = compute_bundle_hash(bundle_root)
    _write_json(manifest_path, manifest)


def _hash_payload(payload: Any) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="afriride-pilot")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build-sample-bundle")
    build_parser.add_argument("--output", required=True)

    validate_parser = subparsers.add_parser("validate-bundle")
    validate_parser.add_argument("--bundle", required=True)

    receipt_parser = subparsers.add_parser("generate-receipt")
    receipt_parser.add_argument("--bundle", required=True)
    receipt_parser.add_argument("--output", required=True)

    cert_parser = subparsers.add_parser("certify")
    cert_parser.add_argument("--bundle", required=True)
    cert_parser.add_argument("--receipt", required=True)
    cert_parser.add_argument("--output", required=True)

    args = parser.parse_args(argv)

    try:
        if args.command == "build-sample-bundle":
            path = build_sample_bundle(Path(args.output))
            print(f"EVIDENCE BUNDLE VALID: {path}")
        elif args.command == "validate-bundle":
            report = validate_bundle(Path(args.bundle))
            print(f"EVIDENCE BUNDLE VALID: {report.bundle_id}")
        elif args.command == "generate-receipt":
            path = generate_execution_receipt(Path(args.bundle), Path(args.output))
            print(f"EXECUTION RECEIPT VALID: {path}")
        elif args.command == "certify":
            path = generate_certificate(Path(args.bundle), Path(args.receipt), Path(args.output))
            print(f"CONTROLLED PILOT CERTIFICATE VALID: {path}")
    except RuntimeError as exc:
        print(f"AFRIRIDE PILOT CLI REJECTED: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
