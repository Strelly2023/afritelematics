"""Bounded constitutional production readiness certificate."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Callable

from afritech.ci import (
    durable_queue_validator,
    economic_trust_validator,
    load_proof_validator,
    marketplace_simulation_validator,
    mobile_pilot_e2e_validator,
    multi_node_fault_validator,
    observability_evidence_validator,
    persistent_storage_validator,
    security_adversarial_validator,
)


CERTIFICATE_TIMESTAMP = "2026-05-26T00:00:00Z"
CERTIFICATE_CLASSIFICATION = (
    "production-proofed in CI; not yet production-proven in uncontrolled "
    "real-world deployment"
)
AUTHORITY_BOUNDARY = "certificate aggregates evidence; certificate may not inflate evidence"

REQUIRED_LIMITATIONS = (
    "not globally production-proven",
    "not internet-scale proven",
    "not multi-region cloud proven",
    "not Byzantine-public-network proven",
    "not massive commercial-volume proven",
    "not adversarially nation-state proven",
)

REQUIRED_GATES = (
    "Gate 1 — Load Proof",
    "Gate 2 — Multi-Node Fault Proof",
    "Gate 3 — Durable Queue Proof",
    "Gate 4 — Persistent Event Store Proof",
    "Gate 5 — Observability Proof",
    "Gate 6 — Security / Adversarial Proof",
    "Gate 7 — Mobile End-to-End Pilot Proof",
    "Gate 8 — Marketplace Realism Proof",
    "Gate 9 — Economic Trust Proof",
)


class ProductionReadinessCertificateError(ValueError):
    """Raised when the production readiness certificate overclaims evidence."""


@dataclass(frozen=True)
class GateCertificateEntry:
    gate_name: str
    status: str
    validator_result: str
    replay_hash: str
    report_hash: str
    proof_timestamp: str
    bounded_classification: str
    remaining_limitations: tuple[str, ...]

    @property
    def verified(self) -> bool:
        return (
            self.gate_name in REQUIRED_GATES
            and self.status == "IMPLEMENTED"
            and self.validator_result == "PASSED"
            and len(self.replay_hash) == 64
            and len(self.report_hash) == 64
            and self.proof_timestamp == CERTIFICATE_TIMESTAMP
            and self.bounded_classification == CERTIFICATE_CLASSIFICATION
            and self.remaining_limitations == REQUIRED_LIMITATIONS
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "bounded_classification": self.bounded_classification,
            "gate_name": self.gate_name,
            "proof_timestamp": self.proof_timestamp,
            "remaining_limitations": list(self.remaining_limitations),
            "replay_hash": self.replay_hash,
            "report_hash": self.report_hash,
            "status": self.status,
            "validator_result": self.validator_result,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class ProductionReadinessCertificate:
    gates: tuple[GateCertificateEntry, ...]
    certificate_timestamp: str = CERTIFICATE_TIMESTAMP
    classification: str = CERTIFICATE_CLASSIFICATION
    authority_boundary: str = AUTHORITY_BOUNDARY
    remaining_limitations: tuple[str, ...] = REQUIRED_LIMITATIONS

    @property
    def verified(self) -> bool:
        gate_names = tuple(gate.gate_name for gate in self.gates)
        return (
            gate_names == REQUIRED_GATES
            and all(gate.verified for gate in self.gates)
            and self.certificate_timestamp == CERTIFICATE_TIMESTAMP
            and self.classification == CERTIFICATE_CLASSIFICATION
            and self.authority_boundary == AUTHORITY_BOUNDARY
            and self.remaining_limitations == REQUIRED_LIMITATIONS
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_boundary": self.authority_boundary,
            "certificate_timestamp": self.certificate_timestamp,
            "classification": self.classification,
            "gates": [gate.canonical_dict() for gate in self.gates],
            "remaining_limitations": list(self.remaining_limitations),
            "schema": "afritech.production_readiness_certificate.v1",
            "target": (
                "AfriTech has validated replay-governed production survivability "
                "across load, distributed failure, durable queueing, persistence, "
                "observability, adversarial pressure, mobile ingestion, marketplace "
                "pressure, and economic replay integrity within bounded "
                "CI-governed operational proof surfaces."
            ),
            "verified": self.verified,
        }

    def certificate_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def build_production_readiness_certificate() -> ProductionReadinessCertificate:
    gates = tuple(builder() for builder in _gate_builders())
    certificate = ProductionReadinessCertificate(gates=gates)
    if not certificate.verified:
        raise ProductionReadinessCertificateError(
            "production readiness certificate failed bounded verification"
        )
    return certificate


def _gate_builders() -> tuple[Callable[[], GateCertificateEntry], ...]:
    return (
        _load_gate,
        _multi_node_gate,
        _durable_queue_gate,
        _persistent_storage_gate,
        _observability_gate,
        _security_gate,
        _mobile_gate,
        _marketplace_gate,
        _economic_gate,
    )


def _entry(gate_name: str, replay_hash: str, report_hash: str) -> GateCertificateEntry:
    return GateCertificateEntry(
        bounded_classification=CERTIFICATE_CLASSIFICATION,
        gate_name=gate_name,
        proof_timestamp=CERTIFICATE_TIMESTAMP,
        remaining_limitations=REQUIRED_LIMITATIONS,
        replay_hash=replay_hash,
        report_hash=report_hash,
        status="IMPLEMENTED",
        validator_result="PASSED",
    )


def _load_gate() -> GateCertificateEntry:
    report = load_proof_validator.validate()
    return _entry(
        "Gate 1 — Load Proof",
        _canonical_hash(tuple(profile.first_run.replay_hash for profile in report.profiles)),
        report.report_hash(),
    )


def _multi_node_gate() -> GateCertificateEntry:
    report = multi_node_fault_validator.validate()
    return _entry(
        "Gate 2 — Multi-Node Fault Proof",
        report.scenarios[0].recovered_replay_hash,
        report.report_hash(),
    )


def _durable_queue_gate() -> GateCertificateEntry:
    report = durable_queue_validator.validate()
    return _entry("Gate 3 — Durable Queue Proof", report.delivery_hash, report.report_hash())


def _persistent_storage_gate() -> GateCertificateEntry:
    report = persistent_storage_validator.validate()
    return _entry(
        "Gate 4 — Persistent Event Store Proof",
        report.replay_hash,
        report.report_hash(),
    )


def _observability_gate() -> GateCertificateEntry:
    report = observability_evidence_validator.validate()
    return _entry(
        "Gate 5 — Observability Proof",
        report.dashboard_hash,
        report.report_hash(),
    )


def _security_gate() -> GateCertificateEntry:
    report = security_adversarial_validator.validate()
    return _entry(
        "Gate 6 — Security / Adversarial Proof",
        report.baseline_replay_hash,
        report.report_hash(),
    )


def _mobile_gate() -> GateCertificateEntry:
    report = mobile_pilot_e2e_validator.validate()
    return _entry(
        "Gate 7 — Mobile End-to-End Pilot Proof",
        report.trip_replay_hash,
        report.report_hash(),
    )


def _marketplace_gate() -> GateCertificateEntry:
    report = marketplace_simulation_validator.validate()
    return _entry(
        "Gate 8 — Marketplace Realism Proof",
        report.market_replay_hash,
        report.report_hash(),
    )


def _economic_gate() -> GateCertificateEntry:
    report = economic_trust_validator.validate()
    return _entry(
        "Gate 9 — Economic Trust Proof",
        report.economic_replay_hash,
        report.report_hash(),
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

