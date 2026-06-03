"""AfriRide field validation proof harness."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from afriride.field_validation.device_logger import DeviceLogger
from afriride.field_validation.dispute_runner import FieldDisputeResult, run_dispute
from afriride.field_validation.event_buffer import EventBuffer
from afriride.field_validation.sync_replayer import FieldReplayResult, replay_field_trace
from afritech.replay_authority.engine import DisputeClaim


AUTHORITY_LAW = "Modeled guarantees must not degrade under physical constraints."

REQUIRED_SCENARIOS = (
    "offline_trip",
    "delayed_sync",
    "gps_drift",
    "duplicate_events",
    "dispute_resolution",
)

REPORT_FILES = {
    "offline_trip": "offline_trip.json",
    "delayed_sync": "delayed_sync.json",
    "gps_drift": "gps_drift.json",
    "duplicate_events": "duplicate_events.json",
    "dispute_resolution": "dispute_resolution.json",
}


class AfriRideFieldProofError(RuntimeError):
    """Raised when field-like execution breaks modeled proof invariants."""


@dataclass(frozen=True)
class AfriRideFieldScenarioProof:
    scenario: str
    baseline_trace: tuple[Mapping[str, Any], ...]
    field_trace: tuple[Mapping[str, Any], ...]
    replay: FieldReplayResult
    dispute: FieldDisputeResult | None = None

    @property
    def dispute_match(self) -> bool:
        if self.dispute is None:
            return True
        return (
            self.dispute.admitted is False
            and self.dispute.reason == "claim_conflicts_with_replay_authority"
            and self.dispute.audit_packet.get("verified") is True
        )

    @property
    def verified(self) -> bool:
        return self.replay.verified and self.dispute_match

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_law": AUTHORITY_LAW,
            "baseline_trace": [_canonicalize(event) for event in self.baseline_trace],
            "dispute": self.dispute.canonical_dict() if self.dispute else None,
            "dispute_match": self.dispute_match,
            "field_trace": [_canonicalize(event) for event in self.field_trace],
            "replay": self.replay.canonical_dict(),
            "scenario": self.scenario,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class AfriRideFieldProofReport:
    scenarios: tuple[AfriRideFieldScenarioProof, ...]

    @property
    def verified(self) -> bool:
        return (
            tuple(scenario.scenario for scenario in self.scenarios)
            == REQUIRED_SCENARIOS
            and all(scenario.verified for scenario in self.scenarios)
        )

    @property
    def afriride_field_hash(self) -> str:
        return _canonical_hash(
            {
                "authority_law": AUTHORITY_LAW,
                "scenario_hashes": {
                    scenario.scenario: scenario.report_hash()
                    for scenario in self.scenarios
                },
                "verified": self.verified,
            }
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "afriride_field_hash": self.afriride_field_hash,
            "authority_law": AUTHORITY_LAW,
            "required_scenarios": list(REQUIRED_SCENARIOS),
            "scenarios": [scenario.canonical_dict() for scenario in self.scenarios],
            "schema": "afriride.field_proof_report.v1",
            "verified": self.verified,
        }


def run_afriride_field_proof() -> AfriRideFieldProofReport:
    report = AfriRideFieldProofReport(
        scenarios=tuple(_build_scenario(name) for name in REQUIRED_SCENARIOS)
    )
    if not report.verified:
        raise AfriRideFieldProofError("AfriRide field proof failed")
    return report


def write_afriride_field_proof_reports(
    output_dir: str | Path = "reports/afriride_field_proof_v1",
) -> AfriRideFieldProofReport:
    report = run_afriride_field_proof()
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    for scenario in report.scenarios:
        _write_json(target / REPORT_FILES[scenario.scenario], scenario.canonical_dict())
    _write_json(
        target / "field_equivalence.json",
        {
            "afriride_field_hash": report.afriride_field_hash,
            "authority_law": AUTHORITY_LAW,
            "equivalent": report.verified,
            "scenario_hashes": {
                scenario.scenario: scenario.report_hash()
                for scenario in report.scenarios
            },
            "schema": "afriride.field_equivalence_report.v1",
        },
    )
    return report


def _build_scenario(name: str) -> AfriRideFieldScenarioProof:
    baseline = _baseline_trace()
    field = _field_trace(name, baseline)
    replay = replay_field_trace(baseline, field)
    dispute = None
    if name == "dispute_resolution":
        dispute = run_dispute(
            replay.field_authoritative_trace,
            DisputeClaim(
                asserted_value=9999,
                claim_id="field.claim.rider.fare",
                claimant_id="rider.field.001",
                decision_id="ride.field.001:fare_cents",
                supporting_event_ids=("field.event.002",),
            ),
        )
    return AfriRideFieldScenarioProof(
        baseline_trace=baseline,
        dispute=dispute,
        field_trace=field,
        replay=replay,
        scenario=name,
    )


def _field_trace(
    scenario: str,
    baseline: tuple[Mapping[str, Any], ...],
) -> tuple[Mapping[str, Any], ...]:
    if scenario == "offline_trip":
        return _from_device_logs(
            (
                (baseline[0], True),
                (baseline[1], True),
                (baseline[2], True),
                (baseline[3], False),
                (baseline[4], False),
                (baseline[5], False),
                (baseline[6], True),
            )
        )
    if scenario == "delayed_sync":
        return tuple(
            _with(event, received_order=int(event["sequence"]) + 60, source="delayed_sync")
            if int(event["sequence"]) in (3, 4, 5)
            else event
            for event in baseline
        )
    if scenario == "gps_drift":
        return (
            *baseline[:4],
            _gps_event(30, latitude=-37.8136, longitude=144.9631),
            _gps_event(31, latitude=-37.8100, longitude=144.9600),
            _gps_event(32, latitude=-37.9000, longitude=145.2000),
            *baseline[4:],
        )
    if scenario == "duplicate_events":
        return (
            baseline[0],
            baseline[1],
            baseline[2],
            baseline[2],
            baseline[3],
            baseline[4],
            baseline[4],
            baseline[5],
            baseline[6],
        )
    if scenario == "dispute_resolution":
        return baseline
    raise AfriRideFieldProofError(f"unknown field scenario: {scenario}")


def _from_device_logs(
    events: tuple[tuple[Mapping[str, Any], bool], ...],
) -> tuple[Mapping[str, Any], ...]:
    driver = DeviceLogger(device_id="driver.device.field.001", role="driver")
    rider = DeviceLogger(device_id="rider.device.field.001", role="rider")
    buffer = EventBuffer()
    for event, online in events:
        logger = rider if str(event["identity_id"]).startswith("rider.") else driver
        entry = logger.record(
            event,
            online=online,
            observed_at=f"2026-05-27T00:03:{int(event['sequence']):02d}Z",
        )
        buffer = buffer.append(entry)
    return buffer.synced_events()


def _baseline_trace() -> tuple[Mapping[str, Any], ...]:
    return tuple(_event(index) for index in range(7))


def _event(index: int) -> dict[str, Any]:
    identity = "rider.field.001" if index < 3 else "driver.field.001"
    actions = (
        "request",
        "match",
        "price_quote",
        "accept",
        "pickup",
        "dropoff",
        "complete",
    )
    payload: dict[str, object] = {
        "action": actions[index],
        "ride_id": "ride.field.001",
    }
    if actions[index] == "match":
        payload["driver_id"] = "driver.field.001"
    if actions[index] == "price_quote":
        payload["fare_cents"] = 1900
    return {
        "event_id": f"field.event.{index:03d}",
        "identity_id": identity,
        "partition_id": _canonical_partition(identity),
        "payload": payload,
        "received_order": index,
        "sequence": index,
        "source": "mobile_adapter",
        "source_timestamp": f"2026-05-27T00:03:{index:02d}Z",
    }


def _gps_event(index: int, *, latitude: float, longitude: float) -> dict[str, Any]:
    return {
        "event_id": f"field.gps.{index:03d}",
        "identity_id": "driver.field.001",
        "partition_id": _canonical_partition("driver.field.001"),
        "payload": {
            "action": "gps_update",
            "latitude": latitude,
            "longitude": longitude,
            "ride_id": "ride.field.001",
        },
        "received_order": index,
        "sequence": index,
        "source": "device_gps",
        "source_timestamp": f"2026-05-27T00:03:{index % 60:02d}Z",
    }


def _with(event: Mapping[str, Any], **updates: Any) -> dict[str, Any]:
    clone = dict(event)
    clone.update(updates)
    return clone


def _canonical_partition(identity_id: str) -> str:
    return f"partition.{sum(identity_id.encode('utf-8')) % 4}"


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    return value


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            _canonicalize(value),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def main() -> int:
    try:
        report = write_afriride_field_proof_reports()
    except AfriRideFieldProofError as exc:
        print(f"AfriRide field proof FAILED: {exc}")
        return 1
    print(
        "AfriRide field proof PASSED: "
        f"scenarios={len(report.scenarios)} "
        f"afriride_field_hash={report.afriride_field_hash}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

