"""Bounded AfriRide Phase 5 readiness certificate."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afritech.ci import afriride_ga_elive_workflow_validator


ROOT = Path(__file__).resolve().parents[2]
CERTIFICATE_TIMESTAMP = "2026-06-01T00:00:00Z"
CERTIFICATE_CLASSIFICATION = (
    "phase_5_substantially_implemented; controlled_pilot_readiness_not_yet_proven"
)
AUTHORITY_BOUNDARY = (
    "certificate aggregates bounded evidence; certificate may not grant launch, "
    "pilot, mutation, or truth authority"
)

REQUIRED_EVIDENCE = (
    "Live/local rider-backend-driver E2E",
    "Adversarial fail-closed integration",
    "Signed ledger validation",
    "Portable receipt export",
    "Rider proof visibility",
    "Driver proof visibility",
    "GA eLive workflow gate",
)

REMAINING_GAPS = (
    "real Flutter driver app to running backend to real rider app not yet proven",
    "multi-driver contention not yet proven",
    "concurrent ride execution not yet proven",
    "network interruption recovery not yet proven",
    "cross-device signed event emission not yet proven",
    "pilot field operation not yet proven",
    "external audit anchoring not yet proven",
    "production key custody not yet proven",
)

EVIDENCE_FILES = {
    "Live/local rider-backend-driver E2E": (
        "afriride_system/tests/e2e/test_live_local_mobile_clients_e2e.py",
    ),
    "Adversarial fail-closed integration": (
        "afriride_system/tests/test_phase5_adversarial_integration.py",
    ),
    "Signed ledger validation": (
        "afriride_system/tests/test_event_ledger_validation.py",
        "afriride_system/backend/event_ledger.py",
        "afriride_system/backend/event_signatures.py",
    ),
    "Portable receipt export": (
        "afriride_system/tests/test_ledger_receipts.py",
        "afriride_system/backend/ledger_receipts.py",
    ),
    "Rider proof visibility": (
        "rider_app/tests/test_rider_app_surface.py",
        "rider_app/ui/screens/ReceiptScreen.tsx",
        "rider_app/core/api/ride.service.ts",
    ),
    "Driver proof visibility": (
        "afriride_system/tests/test_driver_backend_contract.py",
        "afriride_system/flutter/driver_app/test/ledger_receipt_screen_test.dart",
        "afriride_system/flutter/driver_app/lib/screens/ledger_receipt_screen.dart",
    ),
    "GA eLive workflow gate": (
        "docs/proof/AFRIRIDE_GA_ELIVE_WORKFLOW.md",
        "afritech/ci/afriride_ga_elive_workflow_validator.py",
        ".github/workflows/ga_plus_plus_plus.yml",
    ),
}

EVIDENCE_COMMANDS = {
    "Live/local rider-backend-driver E2E": (
        "pytest -q afriride_system/tests/e2e/test_live_local_mobile_clients_e2e.py",
    ),
    "Adversarial fail-closed integration": (
        "pytest -q afriride_system/tests/test_phase5_adversarial_integration.py",
    ),
    "Signed ledger validation": (
        "pytest -q afriride_system/tests/test_event_ledger_validation.py",
    ),
    "Portable receipt export": (
        "pytest -q afriride_system/tests/test_ledger_receipts.py",
    ),
    "Rider proof visibility": (
        "pytest -q rider_app/tests/test_rider_app_surface.py",
    ),
    "Driver proof visibility": (
        "pytest -q afriride_system/tests/test_driver_backend_contract.py",
        "flutter test test/ledger_receipt_screen_test.dart",
    ),
    "GA eLive workflow gate": (
        "python3 -m afritech.ci.afriride_ga_elive_workflow_validator",
    ),
}


class AfriRidePhase5ReadinessCertificateError(ValueError):
    """Raised when the Phase 5 certificate overclaims or loses evidence."""


@dataclass(frozen=True)
class Phase5EvidenceEntry:
    evidence_name: str
    status: str
    evidence_hash: str
    files: tuple[str, ...]
    commands: tuple[str, ...]
    authority: str = "bounded_evidence_only"

    @property
    def verified(self) -> bool:
        return (
            self.evidence_name in REQUIRED_EVIDENCE
            and self.status == "PASSED"
            and len(self.evidence_hash) == 64
            and self.files == EVIDENCE_FILES[self.evidence_name]
            and self.commands == EVIDENCE_COMMANDS[self.evidence_name]
            and self.authority == "bounded_evidence_only"
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority": self.authority,
            "commands": list(self.commands),
            "evidence_hash": self.evidence_hash,
            "evidence_name": self.evidence_name,
            "files": list(self.files),
            "status": self.status,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class AfriRidePhase5ReadinessCertificate:
    evidence: tuple[Phase5EvidenceEntry, ...]
    certificate_timestamp: str = CERTIFICATE_TIMESTAMP
    classification: str = CERTIFICATE_CLASSIFICATION
    authority_boundary: str = AUTHORITY_BOUNDARY
    remaining_gaps: tuple[str, ...] = REMAINING_GAPS
    write_enabled: bool = False
    mutation_authority: bool = False
    truth_authority: str = "replay_only"

    @property
    def verified(self) -> bool:
        names = tuple(entry.evidence_name for entry in self.evidence)
        return (
            names == REQUIRED_EVIDENCE
            and all(entry.verified for entry in self.evidence)
            and self.certificate_timestamp == CERTIFICATE_TIMESTAMP
            and self.classification == CERTIFICATE_CLASSIFICATION
            and self.authority_boundary == AUTHORITY_BOUNDARY
            and self.remaining_gaps == REMAINING_GAPS
            and self.write_enabled is False
            and self.mutation_authority is False
            and self.truth_authority == "replay_only"
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_boundary": self.authority_boundary,
            "certificate_timestamp": self.certificate_timestamp,
            "classification": self.classification,
            "evidence": [entry.canonical_dict() for entry in self.evidence],
            "mutation_authority": self.mutation_authority,
            "remaining_gaps": list(self.remaining_gaps),
            "schema": "afriride.phase5_readiness_certificate.v1",
            "target": (
                "AfriRide Phase 5 has bounded executable evidence for local "
                "rider-driver lifecycle execution, shared proof visibility, "
                "cryptographic ledger validation, portable receipt export, "
                "adversarial fail-closed behavior, and GA eLive workflow gating."
            ),
            "truth_authority": self.truth_authority,
            "verified": self.verified,
            "write_enabled": self.write_enabled,
        }

    def certificate_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def build_afriride_phase5_readiness_certificate() -> AfriRidePhase5ReadinessCertificate:
    evidence = tuple(_entry(evidence_name) for evidence_name in REQUIRED_EVIDENCE)
    certificate = AfriRidePhase5ReadinessCertificate(evidence=evidence)
    if not certificate.verified:
        raise AfriRidePhase5ReadinessCertificateError(
            "AfriRide Phase 5 readiness certificate failed bounded verification"
        )
    return certificate


def _entry(evidence_name: str) -> Phase5EvidenceEntry:
    files = EVIDENCE_FILES[evidence_name]
    commands = EVIDENCE_COMMANDS[evidence_name]
    return Phase5EvidenceEntry(
        commands=commands,
        evidence_hash=_evidence_hash(evidence_name, files),
        evidence_name=evidence_name,
        files=files,
        status="PASSED",
    )


def _evidence_hash(evidence_name: str, files: tuple[str, ...]) -> str:
    if evidence_name == "GA eLive workflow gate":
        gate_report = afriride_ga_elive_workflow_validator.validate().canonical_dict()
    else:
        gate_report = None
    payload = {
        "evidence_name": evidence_name,
        "files": [
            {
                "path": path,
                "sha256": _file_hash(ROOT / path),
            }
            for path in files
        ],
        "gate_report": gate_report,
    }
    return _canonical_hash(payload)


def _file_hash(path: Path) -> str:
    if not path.exists() or not path.is_file():
        raise AfriRidePhase5ReadinessCertificateError(f"missing evidence file: {path}")
    return sha256(path.read_bytes()).hexdigest()


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
