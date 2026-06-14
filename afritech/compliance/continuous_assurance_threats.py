"""Threat simulation engine for the continuous assurance contract."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from typing import Any, Callable

from afritech.afripay.external_packages import ProviderCertificationEvidence
from afritech.afripay.external_packages import InvestorTechnicalDossier, RegulatorAuditPackage
from afritech.compliance.continuous_assurance import ContinuousAssurancePackage
from afritech.compliance.continuous_assurance_invariants import (
    ContinuousAssuranceInvariantReport,
    ContinuousAssuranceInvariantError,
    evaluate_continuous_assurance_invariants,
    validate_continuous_assurance_invariants,
)
from afritech.monitoring.realtime_anomaly_alerting import RealtimeAnomalyAlert, build_realtime_anomaly_alerts
from afritech.security.ai_anomaly_engine import detect_ai_anomaly


class ContinuousAssuranceThreatError(RuntimeError):
    """Raised when threat simulation cannot be admitted."""


@dataclass(frozen=True)
class ThreatScenario:
    scenario_id: str
    name: str
    attack_surface: str
    anomaly_events: dict[str, tuple[str, ...]]
    mutate: Callable[[ContinuousAssurancePackage], ContinuousAssurancePackage]


@dataclass(frozen=True)
class ThreatScenarioResult:
    scenario_id: str
    name: str
    attack_surface: str
    baseline_truth_hash: str
    mutated_truth_hash: str
    detected: bool
    invariant_report: ContinuousAssuranceInvariantReport
    anomaly_alerts: tuple[RealtimeAnomalyAlert, ...]
    ai_result: dict[str, Any]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "attack_surface": self.attack_surface,
            "baseline_truth_hash": self.baseline_truth_hash,
            "mutated_truth_hash": self.mutated_truth_hash,
            "detected": self.detected,
            "invariant_report": self.invariant_report.canonical_dict(),
            "anomaly_alerts": [alert.canonical_dict() for alert in self.anomaly_alerts],
            "ai_result": self.ai_result,
        }


@dataclass(frozen=True)
class ThreatSimulationReport:
    package_title: str
    package_hash: str
    scenario_results: tuple[ThreatScenarioResult, ...]
    trust_score: float
    live_ai_risks: tuple[str, ...]

    @property
    def verified(self) -> bool:
        return all(result.detected for result in self.scenario_results) and self.trust_score == 1.0

    @property
    def detected_count(self) -> int:
        return sum(1 for result in self.scenario_results if result.detected)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "package_title": self.package_title,
            "package_hash": self.package_hash,
            "scenario_results": [result.canonical_dict() for result in self.scenario_results],
            "trust_score": round(self.trust_score, 6),
            "live_ai_risks": list(self.live_ai_risks),
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def simulate_continuous_assurance_threats(
    package: ContinuousAssurancePackage,
) -> ThreatSimulationReport:
    try:
        validate_continuous_assurance_invariants(package)
    except ContinuousAssuranceInvariantError as exc:
        raise ContinuousAssuranceThreatError(str(exc)) from exc

    baseline_truth_hash = _canonical_hash(package.canonical_dict())
    scenario_results: list[ThreatScenarioResult] = []
    live_ai_risks: list[str] = []

    for scenario in THREAT_SCENARIOS:
        mutated_package = scenario.mutate(package)
        mutated_truth_hash = _canonical_hash(mutated_package.canonical_dict())
        invariant_report = evaluate_continuous_assurance_invariants(
            mutated_package,
            reference_package=package,
        )
        anomaly_alerts = _build_alerts(scenario, mutated_truth_hash)
        ai_result = _build_ai_result(scenario, package, mutated_package)
        live_ai_risks.append(str(ai_result.get("risk", "UNKNOWN")))

        detected = (
            baseline_truth_hash != mutated_truth_hash
            and not invariant_report.verified
            and bool(anomaly_alerts)
            and bool(ai_result.get("anomaly"))
        )
        scenario_results.append(
            ThreatScenarioResult(
                scenario_id=scenario.scenario_id,
                name=scenario.name,
                attack_surface=scenario.attack_surface,
                baseline_truth_hash=baseline_truth_hash,
                mutated_truth_hash=mutated_truth_hash,
                detected=detected,
                invariant_report=invariant_report,
                anomaly_alerts=anomaly_alerts,
                ai_result=ai_result,
            )
        )

    trust_score = (
        sum(1 for result in scenario_results if result.detected) / len(scenario_results)
        if scenario_results
        else 0.0
    )
    return ThreatSimulationReport(
        package_title=package.title,
        package_hash=package.package_hash,
        scenario_results=tuple(scenario_results),
        trust_score=trust_score,
        live_ai_risks=tuple(sorted(set(live_ai_risks))),
    )


def validate_continuous_assurance_threats(
    package: ContinuousAssurancePackage,
) -> ThreatSimulationReport:
    report = simulate_continuous_assurance_threats(package)
    if not report.verified:
        raise ContinuousAssuranceThreatError("continuous assurance threat simulation failed")
    return report


def _build_alerts(scenario: ThreatScenario, replay_hash: str) -> tuple[RealtimeAnomalyAlert, ...]:
    return build_realtime_anomaly_alerts(
        dict(scenario.anomaly_events),
        ride_id=f"{scenario.scenario_id}.ride",
        trace_id=f"{scenario.scenario_id}.trace",
        event_id=f"{scenario.scenario_id}.event",
        actor_id="continuous_assurance_threat_simulator",
        device_id=f"{scenario.scenario_id}.device",
        replay_hash=replay_hash,
        opened_at="2026-06-14T00:00:00Z",
    )


def _build_ai_result(
    scenario: ThreatScenario,
    package: ContinuousAssurancePackage,
    mutated_package: ContinuousAssurancePackage,
) -> dict[str, Any]:
    context = {
        "failure_count": 7 if "validation" in scenario.attack_surface or "signature" in scenario.attack_surface else 4,
        "requests": 240,
        "latency": 260 if "timestamp" in scenario.attack_surface or "anchor" in scenario.attack_surface else 180,
        "ip_reputation": -6 if "authority" in scenario.attack_surface else -2,
        "package_hash_delta": package.package_hash != mutated_package.package_hash,
        "scenario": scenario.scenario_id,
    }
    return detect_ai_anomaly(context)


def _mutate_evidence_forgery(package: ContinuousAssurancePackage) -> ContinuousAssurancePackage:
    evidence = list(package.external_evidence)
    forged = replace(evidence[0], sha256_hash="f" * 64)
    evidence[0] = forged
    dashboard = deepcopy(package.dashboard)
    dashboard["external_evidence"][0]["sha256_hash"] = "f" * 64
    return replace(package, external_evidence=tuple(evidence), dashboard=dashboard)


def _mutate_timestamp_manipulation(package: ContinuousAssurancePackage) -> ContinuousAssurancePackage:
    dashboard = deepcopy(package.dashboard)
    dashboard["opened_at"] = "1970-01-01T00:00:00Z"
    return replace(package, dashboard=dashboard)


def _mutate_replay_attacker(package: ContinuousAssurancePackage) -> ContinuousAssurancePackage:
    evidence = list(package.external_evidence)
    replayed = evidence + [evidence[0]]
    dashboard = deepcopy(package.dashboard)
    dashboard["external_evidence"] = [item.canonical_dict() for item in replayed]
    return replace(package, external_evidence=tuple(replayed), dashboard=dashboard)


def _mutate_provider_callback_forgery(package: ContinuousAssurancePackage) -> ContinuousAssurancePackage:
    providers = list(deepcopy(package.provider_certification.providers))
    provider = dict(providers[0])
    provider["callback_validation"] = "forged callback accepted"
    providers[0] = provider
    provider_certification = replace(package.provider_certification, providers=tuple(providers))
    return replace(package, provider_certification=provider_certification)


def _mutate_signature_substitution(package: ContinuousAssurancePackage) -> ContinuousAssurancePackage:
    evidence = package.regulator_audit_package.evidence
    substituted = replace(evidence, signature="forged-signature")
    regulator = replace(package.regulator_audit_package, evidence=substituted)
    return replace(package, regulator_audit_package=regulator)


def _mutate_package_truncation(package: ContinuousAssurancePackage) -> ContinuousAssurancePackage:
    if len(package.external_evidence) <= 1:
        return replace(package, external_evidence=tuple(), dashboard={**package.dashboard, "external_evidence": []})
    truncated = package.external_evidence[:-1]
    dashboard = deepcopy(package.dashboard)
    dashboard["external_evidence"] = [item.canonical_dict() for item in truncated]
    dashboard["external_evidence_count"] = len(truncated)
    return replace(package, external_evidence=truncated, dashboard=dashboard)


def _mutate_anchor_corruption(package: ContinuousAssurancePackage) -> ContinuousAssurancePackage:
    evidence = package.provider_certification.evidence
    bundle = replace(evidence.bundle, global_proof_hash="0" * 64)
    corrupted_evidence = replace(evidence, bundle=bundle)
    provider_certification = replace(package.provider_certification, evidence=corrupted_evidence)
    return replace(package, provider_certification=provider_certification)


def _mutate_dashboard_trust_escalation(package: ContinuousAssurancePackage) -> ContinuousAssurancePackage:
    dashboard = deepcopy(package.dashboard)
    dashboard["authority_boundary"] = "dashboard_admin_override"
    dashboard["submission_controls"]["investor_dossier_ready"] = True
    return replace(package, dashboard=dashboard)


THREAT_SCENARIOS: tuple[ThreatScenario, ...] = (
    ThreatScenario(
        scenario_id="TS-001",
        name="Evidence forgery",
        attack_surface="evidence forgery",
        anomaly_events={"validation_failures": ("evidence forgery",)},
        mutate=_mutate_evidence_forgery,
    ),
    ThreatScenario(
        scenario_id="TS-002",
        name="Timestamp manipulation",
        attack_surface="timestamp manipulation",
        anomaly_events={"timing_violations": ("timestamp skew",)},
        mutate=_mutate_timestamp_manipulation,
    ),
    ThreatScenario(
        scenario_id="TS-003",
        name="Replay attacker",
        attack_surface="replay attacker",
        anomaly_events={"replay_mismatches": ("replay delta",)},
        mutate=_mutate_replay_attacker,
    ),
    ThreatScenario(
        scenario_id="TS-004",
        name="Provider callback forgery",
        attack_surface="provider callback forgery",
        anomaly_events={"contract_mismatches": ("provider callback forgery",)},
        mutate=_mutate_provider_callback_forgery,
    ),
    ThreatScenario(
        scenario_id="TS-005",
        name="Signature substitution",
        attack_surface="signature substitution",
        anomaly_events={"validation_failures": ("signature substitution",)},
        mutate=_mutate_signature_substitution,
    ),
    ThreatScenario(
        scenario_id="TS-006",
        name="Package truncation",
        attack_surface="package truncation",
        anomaly_events={"contract_mismatches": ("package truncation",)},
        mutate=_mutate_package_truncation,
    ),
    ThreatScenario(
        scenario_id="TS-007",
        name="Anchor corruption",
        attack_surface="anchor corruption",
        anomaly_events={"validation_failures": ("anchor corruption",)},
        mutate=_mutate_anchor_corruption,
    ),
    ThreatScenario(
        scenario_id="TS-008",
        name="Dashboard trust escalation",
        attack_surface="dashboard trust escalation",
        anomaly_events={"contract_mismatches": ("authority boundary escalation",)},
        mutate=_mutate_dashboard_trust_escalation,
    ),
)


def _canonical_hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


__all__ = [
    "ContinuousAssuranceThreatError",
    "ThreatScenario",
    "ThreatScenarioResult",
    "ThreatSimulationReport",
    "THREAT_SCENARIOS",
    "simulate_continuous_assurance_threats",
    "validate_continuous_assurance_threats",
]
