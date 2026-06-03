"""Validate bounded production readiness certificate."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from afritech.certification.production_readiness_certificate import (
    CERTIFICATE_CLASSIFICATION,
    REQUIRED_GATES,
    REQUIRED_LIMITATIONS,
    ProductionReadinessCertificateError,
    build_production_readiness_certificate,
)


class ProductionReadinessCertificateValidationError(RuntimeError):
    """Raised when production readiness certificate validation fails."""


@dataclass(frozen=True)
class ProductionReadinessCertificateValidationReport:
    gate_count: int
    gate_names: tuple[str, ...]
    certificate_hash: str
    classification: str
    remaining_limitations: tuple[str, ...]

    @property
    def verified(self) -> bool:
        return (
            self.gate_count == len(REQUIRED_GATES)
            and self.gate_names == REQUIRED_GATES
            and len(self.certificate_hash) == 64
            and self.classification == CERTIFICATE_CLASSIFICATION
            and self.remaining_limitations == REQUIRED_LIMITATIONS
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "certificate_hash": self.certificate_hash,
            "classification": self.classification,
            "gate_count": self.gate_count,
            "gate_names": list(self.gate_names),
            "remaining_limitations": list(self.remaining_limitations),
            "schema": "afritech.production_readiness_certificate_validation_report.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> ProductionReadinessCertificateValidationReport:
    report = run_production_readiness_certificate_validation()
    if not report.verified:
        raise ProductionReadinessCertificateValidationError(
            "production readiness certificate validation failed"
        )
    return report


def run_production_readiness_certificate_validation() -> (
    ProductionReadinessCertificateValidationReport
):
    try:
        certificate = build_production_readiness_certificate()
    except ProductionReadinessCertificateError as exc:
        raise ProductionReadinessCertificateValidationError(str(exc)) from exc

    if not certificate.verified:
        raise ProductionReadinessCertificateValidationError(
            "production readiness certificate failed verification"
        )

    return ProductionReadinessCertificateValidationReport(
        certificate_hash=certificate.certificate_hash(),
        classification=certificate.classification,
        gate_count=len(certificate.gates),
        gate_names=tuple(gate.gate_name for gate in certificate.gates),
        remaining_limitations=certificate.remaining_limitations,
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
    except ProductionReadinessCertificateValidationError as exc:
        print(f"Production readiness certificate validation FAILED: {exc}")
        return 1
    print(
        "Production readiness certificate validation PASSED: "
        f"gates={report.gate_count} "
        f"certificate_hash={report.certificate_hash} "
        f"report_hash={report.report_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

