"""Replay authority proof harness."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from afritech.replay_authority.engine.audit_packet import AuditPacket, build_audit_packet
from afritech.replay_authority.engine.dispute_resolver import (
    DisputeClaim,
    DisputeResolution,
    resolve_dispute,
)
from afritech.replay_authority.engine.reconstruct import reconstruct_authority


AUTHORITY_LAW = (
    "All decisions must be reconstructable as authoritative, dispute-grade truth."
)

REQUIRED_SCENARIOS = (
    "trace_reconstruction",
    "dispute_reproducibility",
    "conflicting_claims_resolution",
    "audit_grade_determinism",
)

REPORT_FILES = {
    "trace_reconstruction": "trace_reconstruction.json",
    "dispute_reproducibility": "dispute_reproducibility.json",
    "conflicting_claims_resolution": "conflicting_claims_resolution.json",
    "audit_grade_determinism": "audit_determinism.json",
}


class ReplayAuthorityProofError(RuntimeError):
    """Raised when replay authority proof detects divergence."""


@dataclass(frozen=True)
class ReplayAuthorityScenarioProof:
    scenario: str
    baseline_trace: tuple[Mapping[str, Any], ...]
    observed_trace: tuple[Mapping[str, Any], ...]
    claims: tuple[DisputeClaim, ...]
    baseline_dispute: DisputeResolution
    observed_dispute: DisputeResolution
    audit_packet: AuditPacket

    @property
    def same_replay_authority(self) -> bool:
        return (
            self.baseline_dispute.reconstruction.replay_authority_hash
            == self.observed_dispute.reconstruction.replay_authority_hash
        )

    @property
    def same_resolution(self) -> bool:
        return self.baseline_dispute.resolution_hash == self.observed_dispute.resolution_hash

    @property
    def conflicting_claims_resolved(self) -> bool:
        if self.scenario != "conflicting_claims_resolution":
            return True
        admitted = tuple(
            resolution.claim.claim_id
            for resolution in self.observed_dispute.resolutions
            if resolution.admitted
        )
        rejected = tuple(
            resolution.claim.claim_id
            for resolution in self.observed_dispute.resolutions
            if not resolution.admitted
        )
        return admitted == ("claim.rider.fare",) and rejected == ("claim.driver.fare",)

    @property
    def verified(self) -> bool:
        return (
            self.same_replay_authority
            and self.same_resolution
            and self.conflicting_claims_resolved
            and self.audit_packet.dispute.verified
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "audit_packet": self.audit_packet.canonical_dict(),
            "authority_law": AUTHORITY_LAW,
            "baseline_trace": [_canonicalize(event) for event in self.baseline_trace],
            "claims": [claim.canonical_dict() for claim in self.claims],
            "conflicting_claims_resolved": self.conflicting_claims_resolved,
            "observed_trace": [_canonicalize(event) for event in self.observed_trace],
            "same_replay_authority": self.same_replay_authority,
            "same_resolution": self.same_resolution,
            "scenario": self.scenario,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class ReplayAuthorityProofReport:
    scenarios: tuple[ReplayAuthorityScenarioProof, ...]

    @property
    def verified(self) -> bool:
        return (
            tuple(scenario.scenario for scenario in self.scenarios)
            == REQUIRED_SCENARIOS
            and all(scenario.verified for scenario in self.scenarios)
        )

    @property
    def replay_authority_hash(self) -> str:
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
            "authority_law": AUTHORITY_LAW,
            "replay_authority_hash": self.replay_authority_hash,
            "required_scenarios": list(REQUIRED_SCENARIOS),
            "scenarios": [scenario.canonical_dict() for scenario in self.scenarios],
            "schema": "afritech.replay_authority_proof_report.v1",
            "verified": self.verified,
        }


def run_replay_authority_proof() -> ReplayAuthorityProofReport:
    report = ReplayAuthorityProofReport(
        scenarios=tuple(_build_scenario(name) for name in REQUIRED_SCENARIOS)
    )
    if not report.verified:
        raise ReplayAuthorityProofError("replay authority proof failed")
    return report


def write_replay_authority_proof_reports(
    output_dir: str | Path = "reports/replay_authority_proof_v1",
) -> ReplayAuthorityProofReport:
    report = run_replay_authority_proof()
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    for scenario in report.scenarios:
        _write_json(target / REPORT_FILES[scenario.scenario], scenario.canonical_dict())
    _write_json(
        target / "replay_authority_equivalence.json",
        {
            "authority_law": AUTHORITY_LAW,
            "equivalent": report.verified,
            "replay_authority_hash": report.replay_authority_hash,
            "scenario_hashes": {
                scenario.scenario: scenario.report_hash()
                for scenario in report.scenarios
            },
            "schema": "afritech.replay_authority_equivalence_report.v1",
        },
    )
    return report


def _build_scenario(name: str) -> ReplayAuthorityScenarioProof:
    baseline_trace = _baseline_trace()
    claims = _claims()
    if name == "trace_reconstruction":
        observed_trace = baseline_trace
    elif name == "dispute_reproducibility":
        observed_trace = (*baseline_trace[:3], baseline_trace[1], *reversed(baseline_trace[3:]))
    elif name == "conflicting_claims_resolution":
        observed_trace = baseline_trace
        claims = (
            DisputeClaim(
                asserted_value=1500,
                claim_id="claim.rider.fare",
                claimant_id="rider.authority.001",
                decision_id="ride.authority.001:fare_cents",
                supporting_event_ids=("authority.event.002",),
            ),
            DisputeClaim(
                asserted_value=9999,
                claim_id="claim.driver.fare",
                claimant_id="driver.authority.001",
                decision_id="ride.authority.001:fare_cents",
                supporting_event_ids=("authority.event.002",),
            ),
        )
    elif name == "audit_grade_determinism":
        observed_trace = (
            *_disturbed_trace(),
            _with(
                baseline_trace[2],
                corrupted=True,
                payload={"replay_truth": "forged", "ride_id": "ride.authority.001"},
            ),
        )
    else:
        raise ReplayAuthorityProofError(f"unknown replay authority scenario: {name}")

    baseline_dispute = resolve_dispute(baseline_trace, claims)
    observed_dispute = resolve_dispute(observed_trace, claims)
    audit_packet = build_audit_packet(observed_dispute)
    return ReplayAuthorityScenarioProof(
        audit_packet=audit_packet,
        baseline_dispute=baseline_dispute,
        baseline_trace=baseline_trace,
        claims=claims,
        observed_dispute=observed_dispute,
        observed_trace=observed_trace,
        scenario=name,
    )


def _baseline_trace() -> tuple[Mapping[str, Any], ...]:
    return tuple(_event(index) for index in range(7))


def _disturbed_trace() -> tuple[Mapping[str, Any], ...]:
    trace = _baseline_trace()
    return (
        trace[0],
        _with(trace[1], received_order=15, partition_id="partition.split.authority"),
        trace[2],
        trace[2],
        trace[3],
        trace[4],
        trace[6],
        trace[5],
    )


def _claims() -> tuple[DisputeClaim, ...]:
    return (
        DisputeClaim(
            asserted_value=1500,
            claim_id="claim.rider.fare",
            claimant_id="rider.authority.001",
            decision_id="ride.authority.001:fare_cents",
            supporting_event_ids=("authority.event.002",),
        ),
        DisputeClaim(
            asserted_value="completed",
            claim_id="claim.driver.status",
            claimant_id="driver.authority.001",
            decision_id="ride.authority.001:ride_status",
            supporting_event_ids=tuple(f"authority.event.{index:03d}" for index in range(7)),
        ),
    )


def _event(index: int) -> dict[str, Any]:
    identity = "rider.authority.001" if index < 3 else "driver.authority.001"
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
        "ride_id": "ride.authority.001",
    }
    if actions[index] == "match":
        payload["driver_id"] = "driver.authority.001"
    if actions[index] == "price_quote":
        payload["fare_cents"] = 1500
    return {
        "event_id": f"authority.event.{index:03d}",
        "identity_id": identity,
        "partition_id": _canonical_partition(identity),
        "payload": payload,
        "received_order": index,
        "sequence": index,
        "source": "mobile_adapter",
        "source_timestamp": f"2026-05-27T00:01:{index:02d}Z",
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
        report = write_replay_authority_proof_reports()
    except ReplayAuthorityProofError as exc:
        print(f"Replay authority proof FAILED: {exc}")
        return 1
    print(
        "Replay authority proof PASSED: "
        f"scenarios={len(report.scenarios)} "
        f"replay_authority_hash={report.replay_authority_hash}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

