"""Proof observability for AfriRide field validation.

The dashboard reports proof health. It does not define truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from afriride.field_validation.field_proof import (
    AfriRideFieldProofReport,
    run_afriride_field_proof,
)


AUTHORITY_DISCLAIMER = (
    "Field observability reports proof health. It does not define truth; "
    "replay validation and field validators remain authority."
)

REQUIRED_METRICS = (
    "scenario_count",
    "replay_equivalence_rate",
    "identity_equivalence_rate",
    "pricing_equivalence_rate",
    "admissibility_equivalence_rate",
    "dispute_reproducibility_rate",
    "drift_detection_count",
    "max_observed_event_count",
)


class ProofObservabilityError(ValueError):
    """Raised when proof observability violates its reporting boundary."""


@dataclass(frozen=True)
class FieldProofMetrics:
    scenario_count: int
    replay_equivalence_rate: float
    identity_equivalence_rate: float
    pricing_equivalence_rate: float
    admissibility_equivalence_rate: float
    dispute_reproducibility_rate: float
    drift_detection_count: int
    max_observed_event_count: int

    @property
    def healthy(self) -> bool:
        return (
            self.scenario_count > 0
            and self.replay_equivalence_rate == 1.0
            and self.identity_equivalence_rate == 1.0
            and self.pricing_equivalence_rate == 1.0
            and self.admissibility_equivalence_rate == 1.0
            and self.dispute_reproducibility_rate == 1.0
            and self.drift_detection_count == 0
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "admissibility_equivalence_rate": self.admissibility_equivalence_rate,
            "dispute_reproducibility_rate": self.dispute_reproducibility_rate,
            "drift_detection_count": self.drift_detection_count,
            "healthy": self.healthy,
            "identity_equivalence_rate": self.identity_equivalence_rate,
            "max_observed_event_count": self.max_observed_event_count,
            "pricing_equivalence_rate": self.pricing_equivalence_rate,
            "replay_equivalence_rate": self.replay_equivalence_rate,
            "scenario_count": self.scenario_count,
        }


@dataclass(frozen=True)
class FieldProofDashboard:
    metrics: FieldProofMetrics
    afriride_field_hash: str
    scenario_hashes: Mapping[str, str]
    authority_disclaimer: str = AUTHORITY_DISCLAIMER

    def __post_init__(self) -> None:
        if self.authority_disclaimer != AUTHORITY_DISCLAIMER:
            raise ProofObservabilityError("field observability authority mismatch")
        if len(self.afriride_field_hash) != 64:
            raise ProofObservabilityError("afriride_field_hash must be sha256")
        for name, value in self.scenario_hashes.items():
            if not name or len(value) != 64:
                raise ProofObservabilityError("scenario hashes must be named sha256 values")

    @property
    def dashboard_hash(self) -> str:
        return _canonical_hash(self.canonical_dict(include_hash=False))

    def canonical_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        payload = {
            "afriride_field_hash": self.afriride_field_hash,
            "authority_disclaimer": self.authority_disclaimer,
            "metrics": self.metrics.canonical_dict(),
            "scenario_hashes": dict(sorted(self.scenario_hashes.items())),
            "schema": "afriride.field_proof_dashboard.v1",
        }
        if include_hash:
            payload["dashboard_hash"] = self.dashboard_hash
        return payload


def build_field_proof_dashboard(
    report: AfriRideFieldProofReport | None = None,
) -> FieldProofDashboard:
    if report is None:
        report = run_afriride_field_proof()
    scenario_count = len(report.scenarios)
    metrics = FieldProofMetrics(
        admissibility_equivalence_rate=_rate(
            scenario.replay.admissibility_match for scenario in report.scenarios
        ),
        dispute_reproducibility_rate=_rate(
            scenario.dispute_match for scenario in report.scenarios
        ),
        drift_detection_count=sum(
            0 if scenario.replay.verified and scenario.dispute_match else 1
            for scenario in report.scenarios
        ),
        identity_equivalence_rate=_rate(
            scenario.replay.identity_match for scenario in report.scenarios
        ),
        max_observed_event_count=max(
            scenario.replay.observed_event_count for scenario in report.scenarios
        ),
        pricing_equivalence_rate=_rate(
            scenario.replay.pricing_match for scenario in report.scenarios
        ),
        replay_equivalence_rate=_rate(
            scenario.replay.replay_match for scenario in report.scenarios
        ),
        scenario_count=scenario_count,
    )
    return FieldProofDashboard(
        afriride_field_hash=report.afriride_field_hash,
        metrics=metrics,
        scenario_hashes={
            scenario.scenario: scenario.report_hash() for scenario in report.scenarios
        },
    )


def write_field_proof_dashboard(
    output_path: str | Path = "reports/afriride_field_proof_v1/proof_dashboard.json",
) -> FieldProofDashboard:
    dashboard = build_field_proof_dashboard()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dashboard.canonical_dict(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return dashboard


def _rate(values) -> float:
    items = tuple(values)
    if not items:
        return 0.0
    return sum(1 for item in items if item) / len(items)


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

