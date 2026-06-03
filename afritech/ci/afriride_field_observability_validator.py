"""Validate AfriRide field proof observability."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afriride.field_validation.proof_observability import (
    AUTHORITY_DISCLAIMER,
    REQUIRED_METRICS,
    ProofObservabilityError,
    build_field_proof_dashboard,
)


class AfriRideFieldObservabilityValidationError(RuntimeError):
    """Raised when field observability validation fails."""


@dataclass(frozen=True)
class AfriRideFieldObservabilityValidationReport:
    dashboard_hash: str
    afriride_field_hash: str

    @property
    def verified(self) -> bool:
        return len(self.dashboard_hash) == 64 and len(self.afriride_field_hash) == 64

    def canonical_dict(self) -> dict[str, object]:
        return {
            "afriride_field_hash": self.afriride_field_hash,
            "dashboard_hash": self.dashboard_hash,
            "schema": "afriride.field_observability_validation_report.v1",
            "verified": self.verified,
        }

    def validation_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> AfriRideFieldObservabilityValidationReport:
    try:
        dashboard = build_field_proof_dashboard()
    except ProofObservabilityError as exc:
        raise AfriRideFieldObservabilityValidationError(str(exc)) from exc

    payload = dashboard.canonical_dict()
    metrics = payload.get("metrics")
    if not isinstance(metrics, dict):
        raise AfriRideFieldObservabilityValidationError("dashboard metrics missing")
    missing = tuple(metric for metric in REQUIRED_METRICS if metric not in metrics)
    if missing:
        raise AfriRideFieldObservabilityValidationError(
            f"dashboard missing metrics: {missing}"
        )
    if payload.get("authority_disclaimer") != AUTHORITY_DISCLAIMER:
        raise AfriRideFieldObservabilityValidationError(
            "field observability authority disclaimer mismatch"
        )
    if metrics.get("healthy") is not True:
        raise AfriRideFieldObservabilityValidationError("field proof dashboard unhealthy")

    report = AfriRideFieldObservabilityValidationReport(
        afriride_field_hash=str(payload["afriride_field_hash"]),
        dashboard_hash=str(payload["dashboard_hash"]),
    )
    if not report.verified:
        raise AfriRideFieldObservabilityValidationError(
            "field observability validation report failed"
        )
    return report


def validate_report_file(
    path: Path = Path("reports/afriride_field_proof_v1/proof_dashboard.json"),
) -> None:
    if not path.exists():
        raise AfriRideFieldObservabilityValidationError("missing proof dashboard report")
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = build_field_proof_dashboard().canonical_dict()
    if payload.get("dashboard_hash") != expected.get("dashboard_hash"):
        raise AfriRideFieldObservabilityValidationError("proof dashboard hash mismatch")


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def main() -> int:
    try:
        report = validate()
    except AfriRideFieldObservabilityValidationError as exc:
        print(f"AfriRide field observability validation FAILED: {exc}")
        return 1

    print(
        "AfriRide field observability validation PASSED: "
        f"dashboard_hash={report.dashboard_hash} "
        f"validation_hash={report.validation_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

