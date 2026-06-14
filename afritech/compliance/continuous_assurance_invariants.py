"""Formal invariants for the continuous assurance contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from afritech.compliance.continuous_assurance import (
    ContinuousAssurancePackage,
    ExternalEvidenceArtifact,
    _canonical_hash,
)


EXPECTED_PACKAGE_SCHEMA = "afritech.continuous_assurance_package.v1"
EXPECTED_AUTHORITY_BOUNDARY = "continuous_assurance_evidence_only"
EXPECTED_DASHBOARD_AUTHORITY_BOUNDARY = "dashboard_reads_external_evidence_and_monitoring_only"
EXPECTED_DASHBOARD_CLASSIFICATION = "CONTINUOUS_ASSURANCE"


class ContinuousAssuranceInvariantError(RuntimeError):
    """Raised when a continuous assurance invariant is violated."""


@dataclass(frozen=True)
class InvariantCheck:
    invariant_id: str
    description: str
    satisfied: bool
    details: str = ""

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "invariant_id": self.invariant_id,
            "description": self.description,
            "satisfied": self.satisfied,
            "details": self.details,
        }


@dataclass(frozen=True)
class ContinuousAssuranceInvariantReport:
    package_title: str
    package_hash: str
    evidence_count: int
    checks: tuple[InvariantCheck, ...]

    @property
    def verified(self) -> bool:
        return all(check.satisfied for check in self.checks)

    @property
    def violations(self) -> tuple[InvariantCheck, ...]:
        return tuple(check for check in self.checks if not check.satisfied)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "package_title": self.package_title,
            "package_hash": self.package_hash,
            "evidence_count": self.evidence_count,
            "checks": [check.canonical_dict() for check in self.checks],
            "verified": self.verified,
        }


def evaluate_continuous_assurance_invariants(
    package: ContinuousAssurancePackage,
    *,
    reference_package: ContinuousAssurancePackage | None = None,
) -> ContinuousAssuranceInvariantReport:
    checks = [
        _check_authority_boundaries(package),
        _check_package_schema(package),
        _check_package_is_evidence_only(package),
        _check_external_evidence_is_untrusted(package),
        _check_missing_evidence_visibility(package),
        _check_dashboard_does_not_mutate_evidence(package),
        _check_package_hash_determinism(package),
    ]

    if reference_package is not None:
        checks.extend(
            [
                _check_same_evidence_set_same_hash(reference_package, package),
                _check_evidence_order_cannot_change_truth(reference_package, package),
                _check_mutation_changes_hash(reference_package, package),
                _check_replay_execution_is_deterministic(reference_package, package),
            ]
        )

    return ContinuousAssuranceInvariantReport(
        package_title=package.title,
        package_hash=package.package_hash,
        evidence_count=len(package.external_evidence),
        checks=tuple(checks),
    )


def validate_continuous_assurance_invariants(
    package: ContinuousAssurancePackage,
    *,
    reference_package: ContinuousAssurancePackage | None = None,
) -> ContinuousAssuranceInvariantReport:
    report = evaluate_continuous_assurance_invariants(
        package,
        reference_package=reference_package,
    )
    if not report.verified:
        details = "; ".join(
            f"{check.invariant_id}: {check.details or check.description}"
            for check in report.violations
        )
        raise ContinuousAssuranceInvariantError(details or "continuous assurance invariants failed")
    return report


def _check_same_evidence_set_same_hash(
    reference: ContinuousAssurancePackage,
    candidate: ContinuousAssurancePackage,
) -> InvariantCheck:
    description = "Same evidence set must produce the same package hash"
    if _evidence_signature(reference.external_evidence) != _evidence_signature(candidate.external_evidence):
        return InvariantCheck(
            "IA-001",
            description,
            satisfied=True,
            details="evidence sets differ; invariant checked by mutation rule",
        )
    satisfied = reference.package_hash == candidate.package_hash
    return InvariantCheck(
        "IA-001",
        description,
        satisfied=satisfied,
        details="" if satisfied else "package hash changed for identical evidence set",
    )


def _check_evidence_order_cannot_change_truth(
    reference: ContinuousAssurancePackage,
    candidate: ContinuousAssurancePackage,
) -> InvariantCheck:
    description = "Evidence order must not change truth"
    reference_signature = _evidence_signature(reference.external_evidence)
    candidate_signature = _evidence_signature(candidate.external_evidence)
    if reference_signature != candidate_signature:
        return InvariantCheck(
            "IA-002",
            description,
            satisfied=True,
            details="evidence content differs; order invariance not applicable",
        )
    satisfied = reference_signature == candidate_signature and reference.package_hash == candidate.package_hash
    return InvariantCheck(
        "IA-002",
        description,
        satisfied=satisfied,
        details="" if satisfied else "canonical evidence ordering or hash diverged",
    )


def _check_mutation_changes_hash(
    reference: ContinuousAssurancePackage,
    candidate: ContinuousAssurancePackage,
) -> InvariantCheck:
    description = "Evidence mutation must change the package hash"
    same_signature = _evidence_signature(reference.external_evidence) == _evidence_signature(candidate.external_evidence)
    if same_signature:
        return InvariantCheck(
            "IA-003",
            description,
            satisfied=True,
            details="evidence set unchanged; mutation rule not applicable",
        )
    satisfied = reference.package_hash != candidate.package_hash
    return InvariantCheck(
        "IA-003",
        description,
        satisfied=satisfied,
        details="" if satisfied else "evidence changed without package hash change",
    )


def _check_dashboard_does_not_mutate_evidence(package: ContinuousAssurancePackage) -> InvariantCheck:
    description = "Dashboard must not mutate evidence"
    dashboard_evidence = package.dashboard.get("external_evidence", [])
    package_evidence = [item.canonical_dict() for item in package.external_evidence]
    satisfied = dashboard_evidence == package_evidence
    return InvariantCheck(
        "IA-004",
        description,
        satisfied=satisfied,
        details="" if satisfied else "dashboard evidence diverged from package evidence",
    )


def _check_package_is_evidence_only(package: ContinuousAssurancePackage) -> InvariantCheck:
    description = "Continuous assurance package must remain evidence-only"
    dashboard = package.dashboard
    allowed_dashboard_keys = {
        "view",
        "classification",
        "authority_boundary",
        "monitoring_status",
        "anomaly_status",
        "submission_ready",
        "regulator_ready",
        "external_evidence",
        "external_evidence_count",
        "anomaly_alert_counts",
        "evidence_controls",
        "submission_controls",
    }
    dashboard_keys = set(dashboard.keys())
    payload = package.canonical_dict()
    allowed_package_keys = {
        "authority_boundary",
        "dashboard",
        "external_evidence",
        "investor_dossier",
        "package_hash",
        "provider_certification",
        "regulator_audit_package",
        "schema",
        "title",
    }
    satisfied = (
        set(payload.keys()) == allowed_package_keys
        and dashboard_keys == allowed_dashboard_keys
        and package.external_evidence is not None
    )
    return InvariantCheck(
        "IA-005",
        description,
        satisfied=satisfied,
        details="" if satisfied else "package or dashboard contains non-contract fields",
    )


def _check_external_evidence_is_untrusted(package: ContinuousAssurancePackage) -> InvariantCheck:
    description = "External evidence must never be automatically trusted"
    evidence = package.external_evidence
    controls = package.dashboard.get("evidence_controls", {})
    satisfied = bool(evidence) and all(
        item.collected_from == "outside_repository" for item in evidence
    ) and controls.get("outside_repository_collection") is True
    return InvariantCheck(
        "IA-006",
        description,
        satisfied=satisfied,
        details="" if satisfied else "external evidence trust boundary missing or unsafe",
    )


def _check_missing_evidence_visibility(package: ContinuousAssurancePackage) -> InvariantCheck:
    description = "Missing evidence must fail visibly"
    satisfied = len(package.external_evidence) > 0
    return InvariantCheck(
        "IA-007",
        description,
        satisfied=satisfied,
        details="" if satisfied else "package carries no external evidence",
    )


def _check_authority_boundaries(package: ContinuousAssurancePackage) -> InvariantCheck:
    description = "Authority boundaries must always be present"
    dashboard = package.dashboard
    satisfied = (
        package.authority_boundary == EXPECTED_AUTHORITY_BOUNDARY
        and dashboard.get("authority_boundary") == EXPECTED_DASHBOARD_AUTHORITY_BOUNDARY
        and dashboard.get("classification") == EXPECTED_DASHBOARD_CLASSIFICATION
    )
    return InvariantCheck(
        "IA-008",
        description,
        satisfied=satisfied,
        details="" if satisfied else "authority boundary or classification mismatch",
    )


def _check_package_schema(package: ContinuousAssurancePackage) -> InvariantCheck:
    description = "Package schema must remain stable"
    satisfied = package.canonical_dict().get("schema") == EXPECTED_PACKAGE_SCHEMA
    return InvariantCheck(
        "IA-009",
        description,
        satisfied=satisfied,
        details="" if satisfied else "schema drift detected",
    )


def _check_package_hash_determinism(package: ContinuousAssurancePackage) -> InvariantCheck:
    description = "Package hash must be deterministic"
    expected_hash = _canonical_hash(
        {
            "title": package.title,
            "dashboard": package.dashboard,
            "external_evidence": [item.canonical_dict() for item in package.external_evidence],
            "regulator_audit_package": package.regulator_audit_package.canonical_dict(),
            "investor_dossier": package.investor_dossier.canonical_dict(),
            "provider_certification": package.provider_certification.canonical_dict(),
        }
    )
    satisfied = expected_hash == package.package_hash
    return InvariantCheck(
        "IA-010",
        description,
        satisfied=satisfied,
        details="" if satisfied else "package hash does not match canonical recomputation",
    )


def _check_replay_execution_is_deterministic(
    reference: ContinuousAssurancePackage,
    candidate: ContinuousAssurancePackage,
) -> InvariantCheck:
    description = "Replay execution must be deterministic"
    same_signature = _evidence_signature(reference.external_evidence) == _evidence_signature(candidate.external_evidence)
    if not same_signature:
        return InvariantCheck(
            "IA-011",
            description,
            satisfied=True,
            details="evidence content differs; replay determinism not applicable",
        )
    satisfied = reference.package_hash == candidate.package_hash
    return InvariantCheck(
        "IA-011",
        description,
        satisfied=satisfied,
        details="" if satisfied else "replay execution diverged for identical evidence",
    )


def _evidence_signature(evidence: Iterable[ExternalEvidenceArtifact]) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (
            item.source_name,
            item.artifact_type,
            item.path,
            item.sha256_hash,
            item.byte_count,
            item.collected_from,
            item.notes,
        )
        for item in evidence
    )


__all__ = [
    "ContinuousAssuranceInvariantError",
    "InvariantCheck",
    "ContinuousAssuranceInvariantReport",
    "evaluate_continuous_assurance_invariants",
    "validate_continuous_assurance_invariants",
]
