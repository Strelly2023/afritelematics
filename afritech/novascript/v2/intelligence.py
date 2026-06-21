from __future__ import annotations

from hashlib import sha256
from typing import Any


class DeploymentFeedbackLoop:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str], list[dict[str, Any]]] = {}

    def record(
        self,
        *,
        organization_id: str,
        project_id: str,
        environment: str,
        status: str,
        validation_score: int,
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        key = (organization_id, project_id)
        sequence = len(self._records.get(key, [])) + 1
        record = {
            "feedback_id": "deployfb-" + sha256(
                f"{organization_id}:{project_id}:{sequence}:{environment}:{status}:{validation_score}".encode("utf-8")
            ).hexdigest()[:12],
            "sequence": sequence,
            "organization_id": organization_id,
            "project_id": project_id,
            "environment": environment,
            "status": status,
            "validation_score": max(0, min(100, int(validation_score))),
            "evidence": evidence or {},
        }
        self._records.setdefault(key, []).append(record)
        return record

    def snapshot(self, *, organization_id: str, project_id: str) -> dict[str, Any]:
        records = self._records.get((organization_id, project_id), [])
        scores = [int(item["validation_score"]) for item in records]
        success_count = len([item for item in records if item["status"] in {"passed", "healthy", "validated"}])
        return {
            "mode": "deployment_feedback_loop",
            "project_id": project_id,
            "feedback_count": len(records),
            "success_rate": round(success_count / len(records), 2) if records else None,
            "average_validation_score": round(sum(scores) / len(scores), 2) if scores else None,
            "recent": records[-5:],
        }


class ContinuousRepositoryIntelligence:
    def analyze(
        self,
        *,
        project_id: str,
        graph: dict[str, Any],
        debt: dict[str, Any],
        memory: dict[str, Any],
        trust: dict[str, Any],
        deployment_feedback: dict[str, Any],
    ) -> dict[str, Any]:
        signals = graph.get("signals", {})
        debt_score = int(debt.get("score", 0))
        trust_score = int(trust.get("trust_score", 0))
        feedback_score = deployment_feedback.get("average_validation_score")
        architecture_version = 1 + int(memory.get("memory_count", 0))
        risk_score = _risk_score(debt_score, trust_score, feedback_score)
        return {
            "mode": "continuous_repository_intelligence",
            "project_id": project_id,
            "architecture_evolution": {
                "architecture_version": architecture_version,
                "change_pressure": _level(debt_score),
                "tracked_signals": signals,
            },
            "engineering_risk": {
                "risk_score": risk_score,
                "risk_level": _level(risk_score),
                "drivers": _risk_drivers(debt_score, trust_score, feedback_score),
            },
            "technical_debt_prediction": {
                "current_score": debt_score,
                "predicted_next_score": min(100, debt_score + max(0, risk_score - 50) // 5),
                "direction": "rising" if risk_score >= 60 else "stable",
            },
            "trust_forecast": _trust_forecast(trust_score, feedback_score),
            "enterprise_knowledge_graph": _knowledge_graph(project_id, graph),
            "autonomous_workflows": _workflow_recommendations(risk_score, debt_score),
        }


class ContinuousAssuranceEngine:
    def assess(
        self,
        *,
        project_id: str,
        trust: dict[str, Any],
        risk: dict[str, Any],
        policy_decision: dict[str, Any],
        architecture: dict[str, Any],
    ) -> dict[str, Any]:
        trust_score = int(trust.get("trust_score", 0))
        risk_score = int(risk.get("risk_score", 0))
        architecture_version = int(architecture.get("architecture_version", 1))
        return {
            "mode": "continuous_assurance",
            "project_id": project_id,
            "trust_drift": _drift(80 - trust_score),
            "risk_drift": _drift(risk_score - 50),
            "policy_drift": "none" if policy_decision.get("allowed") else "policy_violation",
            "architecture_drift": "evolving" if architecture_version > 1 else "baseline",
            "assurance_status": "assured" if trust_score >= 70 and risk_score <= 60 and policy_decision.get("allowed") else "review",
        }


class ArchitectureEvolutionLedger:
    def __init__(self) -> None:
        self._records: dict[str, list[dict[str, Any]]] = {}

    def record(
        self,
        *,
        project_id: str,
        architecture: dict[str, Any],
        decision: dict[str, Any],
        knowledge_graph: dict[str, Any],
    ) -> dict[str, Any]:
        sequence = len(self._records.get(project_id, [])) + 1
        entry = {
            "ledger_id": "archledger-" + sha256(f"{project_id}:{sequence}".encode()).hexdigest()[:12],
            "sequence": sequence,
            "project_id": project_id,
            "architecture_version": architecture.get("architecture_version", sequence),
            "decision_id": decision.get("decision_id"),
            "knowledge_graph_id": knowledge_graph.get("graph_id"),
            "change_pressure": architecture.get("change_pressure"),
        }
        self._records.setdefault(project_id, []).append(entry)
        return {
            "mode": "architecture_evolution_ledger",
            "project_id": project_id,
            "latest": entry,
            "timeline": self._records[project_id][-10:],
        }


def _risk_score(debt_score: int, trust_score: int, feedback_score: Any) -> int:
    feedback_penalty = 0 if feedback_score is None else max(0, 85 - int(feedback_score)) // 2
    return max(0, min(100, debt_score + max(0, 80 - trust_score) // 2 + feedback_penalty))


def _level(score: int) -> str:
    if score >= 75:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def _risk_drivers(debt_score: int, trust_score: int, feedback_score: Any) -> list[str]:
    drivers = []
    if debt_score >= 45:
        drivers.append("technical debt pressure")
    if trust_score < 80:
        drivers.append("trust score below policy target")
    if feedback_score is not None and int(feedback_score) < 85:
        drivers.append("deployment feedback below validation target")
    if not drivers:
        drivers.append("risk within governed bounds")
    return drivers


def _trust_forecast(trust_score: int, feedback_score: Any) -> dict[str, Any]:
    adjustment = 0 if feedback_score is None else (int(feedback_score) - 85) // 5
    forecast = max(0, min(100, trust_score + adjustment))
    return {
        "current_trust_score": trust_score,
        "forecast_trust_score": forecast,
        "direction": "improving" if forecast > trust_score else "declining" if forecast < trust_score else "stable",
    }


def _knowledge_graph(project_id: str, graph: dict[str, Any]) -> dict[str, Any]:
    nodes = list(graph.get("nodes", []))
    edges = list(graph.get("edges", []))
    graph_hash = sha256(f"{project_id}:{len(nodes)}:{len(edges)}".encode("utf-8")).hexdigest()
    return {
        "graph_id": "kg-" + graph_hash[:12],
        "node_count": len(nodes),
        "edge_count": len(edges),
        "domains": sorted({str(node.get("type", "unknown")) for node in nodes if isinstance(node, dict)}),
    }


def _workflow_recommendations(risk_score: int, debt_score: int) -> list[dict[str, Any]]:
    workflows = [{"name": "receipt_verification", "priority": "required"}]
    if debt_score >= 45:
        workflows.append({"name": "debt_reduction_plan", "priority": "high"})
    if risk_score >= 60:
        workflows.append({"name": "governance_review", "priority": "high"})
    else:
        workflows.append({"name": "continuous_repo_scan", "priority": "normal"})
    return workflows


def _drift(delta: int) -> str:
    if delta >= 20:
        return "high"
    if delta >= 8:
        return "medium"
    return "low"


_DEFAULT_DEPLOYMENT_FEEDBACK = DeploymentFeedbackLoop()
_DEFAULT_REPOSITORY_INTELLIGENCE = ContinuousRepositoryIntelligence()
_DEFAULT_ASSURANCE_ENGINE = ContinuousAssuranceEngine()
_DEFAULT_ARCHITECTURE_LEDGER = ArchitectureEvolutionLedger()


def get_deployment_feedback_loop() -> DeploymentFeedbackLoop:
    return _DEFAULT_DEPLOYMENT_FEEDBACK


def get_continuous_repository_intelligence() -> ContinuousRepositoryIntelligence:
    return _DEFAULT_REPOSITORY_INTELLIGENCE


def get_continuous_assurance_engine() -> ContinuousAssuranceEngine:
    return _DEFAULT_ASSURANCE_ENGINE


def get_architecture_evolution_ledger() -> ArchitectureEvolutionLedger:
    return _DEFAULT_ARCHITECTURE_LEDGER
