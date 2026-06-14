"""Deterministic trust scoring for the continuous assurance contract."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from afritech.compliance.assurance_binding_registry import (
    build_assurance_binding_registry,
    validate_assurance_binding_registry,
)
from afritech.compliance.continuous_assurance import ContinuousAssurancePackage
from afritech.compliance.continuous_assurance_invariants import (
    ContinuousAssuranceInvariantReport,
    evaluate_continuous_assurance_invariants,
)
from afritech.compliance.continuous_assurance_threats import (
    ThreatSimulationReport,
    ContinuousAssuranceThreatError,
    validate_continuous_assurance_threats,
)
from afritech.ci.continuous_assurance_proof_validator import (
    ContinuousAssuranceProofReport,
    validate as validate_continuous_assurance_proof,
)


SCHEMA = "afritech.continuous_assurance_trust_report.v1"
AUTHORITY_BOUNDARY = "continuous_assurance_trust_read_only"
TRUST_THRESHOLD = 95.0


class TrustScoringError(RuntimeError):
    """Raised when trust scoring cannot be admitted."""


@dataclass(frozen=True)
class TrustScoreComponent:
    name: str
    weight: float
    score: float
    rationale: str
    source_hash: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "weight": round(self.weight, 6),
            "score": round(self.score, 6),
            "rationale": self.rationale,
            "source_hash": self.source_hash,
        }


@dataclass(frozen=True)
class TrustScoringReport:
    title: str
    package_hash: str
    registry_hash: str
    invariant_report_hash: str
    threat_report_hash: str
    proof_report_hash: str
    components: tuple[TrustScoreComponent, ...]
    trust_score: float
    trust_grade: str
    authority_boundary: str = AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return (
            len(self.package_hash) == 64
            and len(self.registry_hash) == 64
            and len(self.invariant_report_hash) == 64
            and len(self.threat_report_hash) == 64
            and len(self.proof_report_hash) == 64
            and self.trust_score >= TRUST_THRESHOLD
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "components": [component.canonical_dict() for component in self.components],
            "invariant_report_hash": self.invariant_report_hash,
            "package_hash": self.package_hash,
            "proof_report_hash": self.proof_report_hash,
            "registry_hash": self.registry_hash,
            "schema": SCHEMA,
            "title": self.title,
            "threat_report_hash": self.threat_report_hash,
            "trust_grade": self.trust_grade,
            "trust_score": round(self.trust_score, 6),
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def assess_continuous_assurance_trust(
    package: ContinuousAssurancePackage,
    *,
    invariant_report: ContinuousAssuranceInvariantReport | None = None,
    threat_report: ThreatSimulationReport | None = None,
    proof_report: ContinuousAssuranceProofReport | None = None,
    registry: Mapping[str, Any] | dict[str, Any] | None = None,
) -> TrustScoringReport:
    if not isinstance(package, ContinuousAssurancePackage):
        raise TrustScoringError("package must be a ContinuousAssurancePackage")
    registry_payload = build_assurance_binding_registry() if registry is None else _coerce_mapping(registry)
    validate_assurance_binding_registry(registry_payload)

    if invariant_report is None:
        invariant_report = evaluate_continuous_assurance_invariants(package)
    if threat_report is None:
        try:
            threat_report = validate_continuous_assurance_threats(package)
        except ContinuousAssuranceThreatError:
            threat_report = ThreatSimulationReport(
                package_title=package.title,
                package_hash=package.package_hash,
                scenario_results=tuple(),
                trust_score=0.0,
                live_ai_risks=("UNKNOWN",),
            )
    if proof_report is None:
        proof_report = validate_continuous_assurance_proof()

    registry_hash = str(registry_payload["registry_hash"])
    binding_integrity = _score_boolean(
        name="binding_integrity",
        satisfied=registry_hash == registry_payload["registry_hash"],
        rationale="binding registry is canonical and traceable",
        source_hash=registry_hash,
        weight=0.15,
    )

    invariant_integrity_score = _fraction_score(
        satisfied=sum(1 for check in invariant_report.checks if check.satisfied),
        total=len(invariant_report.checks),
    )
    invariant_integrity = TrustScoreComponent(
        name="invariant_integrity",
        weight=0.25,
        score=invariant_integrity_score,
        rationale="formal invariant pass rate",
        source_hash=_canonical_hash(invariant_report.canonical_dict()),
    )

    threat_detection_rate = _fraction_score(
        satisfied=threat_report.detected_count,
        total=len(threat_report.scenario_results),
    )
    threat_detection = TrustScoreComponent(
        name="threat_detection_rate",
        weight=0.25,
        score=threat_detection_rate,
        rationale="threat scenarios detected by simulation",
        source_hash=threat_report.report_hash(),
    )

    proof_validity = _score_boolean(
        name="proof_validity",
        satisfied=(
            proof_report.verified is True
            and proof_report.registry_hash == registry_hash
            and len(proof_report.proof_hash) == 64
        ),
        rationale="proof validator and registry hash alignment",
        source_hash=_canonical_hash(proof_report.canonical_dict()),
        weight=0.20,
    )

    anomaly_health_score = _anomaly_health_score(package)
    anomaly_health = TrustScoreComponent(
        name="anomaly_health",
        weight=0.10,
        score=anomaly_health_score,
        rationale="monitoring anomaly posture",
        source_hash=_canonical_hash(package.dashboard),
    )

    evidence_completeness_score = _evidence_completeness_score(package.dashboard.get("evidence_controls", {}), len(package.external_evidence))
    evidence_completeness = TrustScoreComponent(
        name="evidence_completeness",
        weight=0.05,
        score=evidence_completeness_score,
        rationale="external evidence quality and control coverage",
        source_hash=_canonical_hash(
            {
                "external_evidence": [item.canonical_dict() for item in package.external_evidence],
                "evidence_controls": package.dashboard.get("evidence_controls", {}),
            }
        ),
    )

    trust_score = round(
        100.0
        * sum(
            component.score * component.weight
            for component in (
                binding_integrity,
                invariant_integrity,
                threat_detection,
                proof_validity,
                anomaly_health,
                evidence_completeness,
            )
        ),
        6,
    )
    trust_grade = _trust_grade(trust_score)
    report = TrustScoringReport(
        title="AfriPay Continuous Assurance Trust Score",
        package_hash=package.package_hash,
        registry_hash=registry_hash,
        invariant_report_hash=_canonical_hash(invariant_report.canonical_dict()),
        threat_report_hash=threat_report.report_hash(),
        proof_report_hash=_canonical_hash(proof_report.canonical_dict()),
        components=(
            binding_integrity,
            invariant_integrity,
            threat_detection,
            proof_validity,
            anomaly_health,
            evidence_completeness,
        ),
        trust_score=trust_score,
        trust_grade=trust_grade,
    )
    return report


def validate_continuous_assurance_trust(
    package: ContinuousAssurancePackage,
    *,
    invariant_report: ContinuousAssuranceInvariantReport | None = None,
    threat_report: ThreatSimulationReport | None = None,
    proof_report: ContinuousAssuranceProofReport | None = None,
    registry: Mapping[str, Any] | dict[str, Any] | None = None,
) -> TrustScoringReport:
    report = assess_continuous_assurance_trust(
        package,
        invariant_report=invariant_report,
        threat_report=threat_report,
        proof_report=proof_report,
        registry=registry,
    )
    if not report.verified:
        raise TrustScoringError("continuous assurance trust score failed admission")
    return report


def export_trust_scoring_artifact(report: TrustScoringReport, output_dir: str | Path) -> dict[str, Path]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "continuous_assurance_trust.json"
    json_path.write_text(
        json.dumps(report.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return {"json": json_path}


def _anomaly_health_score(package: ContinuousAssurancePackage) -> float:
    counts = package.dashboard.get("anomaly_alert_counts", {})
    total_alerts = int(counts.get("total", 0) or 0)
    if package.dashboard.get("monitoring_status") == "GREEN" and package.dashboard.get("anomaly_status") == "GREEN" and total_alerts == 0:
        return 1.0
    return max(0.0, 1.0 - min(total_alerts, 10) / 10.0)


def _evidence_completeness_score(evidence_controls: Mapping[str, Any] | dict[str, Any], evidence_count: int) -> float:
    controls = dict(evidence_controls)
    required_flags = (
        "outside_repository_collection",
        "cryptography_review_attached",
        "penetration_test_attached",
        "provider_certification_attached",
        "incident_exercises_attached",
        "compliance_assessment_attached",
    )
    control_ratio = sum(1 for flag in required_flags if controls.get(flag) is True) / len(required_flags)
    evidence_ratio = min(1.0, evidence_count / 5.0)
    return round((control_ratio + evidence_ratio) / 2.0, 6)


def _score_boolean(*, name: str, satisfied: bool, rationale: str, source_hash: str, weight: float) -> TrustScoreComponent:
    return TrustScoreComponent(
        name=name,
        weight=weight,
        score=1.0 if satisfied else 0.0,
        rationale=rationale,
        source_hash=source_hash,
    )


def _fraction_score(*, satisfied: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(max(0.0, min(1.0, satisfied / total)), 6)


def _trust_grade(score: float) -> str:
    if score >= 97.0:
        return "MAXIMUM"
    if score >= 90.0:
        return "HIGH"
    if score >= 75.0:
        return "MODERATE"
    return "LOW"


def _coerce_mapping(value: Mapping[str, Any] | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return dict(value)


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


__all__ = [
    "AUTHORITY_BOUNDARY",
    "SCHEMA",
    "TRUST_THRESHOLD",
    "TrustScoreComponent",
    "TrustScoringError",
    "TrustScoringReport",
    "assess_continuous_assurance_trust",
    "validate_continuous_assurance_trust",
    "export_trust_scoring_artifact",
]
