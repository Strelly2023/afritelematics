"""Validate the bounded AfriRide Phase 5 readiness certificate."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from afritech.certification.afriride_phase5_readiness_certificate import (
    CERTIFICATE_CLASSIFICATION,
    REMAINING_GAPS,
    REQUIRED_EVIDENCE,
    AfriRidePhase5ReadinessCertificateError,
    build_afriride_phase5_readiness_certificate,
)


class AfriRidePhase5ReadinessCertificateValidationError(RuntimeError):
    """Raised when the Phase 5 readiness certificate is not admissible."""


@dataclass(frozen=True)
class AfriRidePhase5ReadinessCertificateValidationReport:
    evidence_count: int
    evidence_names: tuple[str, ...]
    certificate_hash: str
    classification: str
    remaining_gaps: tuple[str, ...]
    truth_authority: str

    @property
    def verified(self) -> bool:
        return (
            self.evidence_count == len(REQUIRED_EVIDENCE)
            and self.evidence_names == REQUIRED_EVIDENCE
            and len(self.certificate_hash) == 64
            and self.classification == CERTIFICATE_CLASSIFICATION
            and self.remaining_gaps == REMAINING_GAPS
            and self.truth_authority == "replay_only"
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "certificate_hash": self.certificate_hash,
            "classification": self.classification,
            "evidence_count": self.evidence_count,
            "evidence_names": list(self.evidence_names),
            "remaining_gaps": list(self.remaining_gaps),
            "schema": "afriride.phase5_readiness_certificate_validation_report.v1",
            "truth_authority": self.truth_authority,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> AfriRidePhase5ReadinessCertificateValidationReport:
    report = run_afriride_phase5_readiness_certificate_validation()
    if not report.verified:
        raise AfriRidePhase5ReadinessCertificateValidationError(
            "AfriRide Phase 5 readiness certificate validation failed"
        )
    return report


def run_afriride_phase5_readiness_certificate_validation() -> (
    AfriRidePhase5ReadinessCertificateValidationReport
):
    try:
        certificate = build_afriride_phase5_readiness_certificate()
    except AfriRidePhase5ReadinessCertificateError as exc:
        raise AfriRidePhase5ReadinessCertificateValidationError(str(exc)) from exc

    if not certificate.verified:
        raise AfriRidePhase5ReadinessCertificateValidationError(
            "AfriRide Phase 5 readiness certificate failed verification"
        )

    return AfriRidePhase5ReadinessCertificateValidationReport(
        certificate_hash=certificate.certificate_hash(),
        classification=certificate.classification,
        evidence_count=len(certificate.evidence),
        evidence_names=tuple(entry.evidence_name for entry in certificate.evidence),
        remaining_gaps=certificate.remaining_gaps,
        truth_authority=certificate.truth_authority,
    )


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
    except AfriRidePhase5ReadinessCertificateValidationError as exc:
        print(f"AfriRide Phase 5 readiness certificate validation FAILED: {exc}")
        return 1
    print(
        "AfriRide Phase 5 readiness certificate validation PASSED: "
        f"evidence={report.evidence_count} "
        f"certificate_hash={report.certificate_hash} "
        f"truth_authority={report.truth_authority} "
        f"report_hash={report.report_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
