from __future__ import annotations

from hashlib import sha256
from typing import Any


class AutonomousRemediationEngine:
    def plan(
        self,
        *,
        project_id: str,
        risk: dict[str, Any],
        debt_prediction: dict[str, Any],
        policy_trust: dict[str, Any],
    ) -> dict[str, Any]:
        actions: list[dict[str, Any]] = []
        if int(risk.get("risk_score", 0)) >= 60:
            actions.append(_action(project_id, "governance_review", "open policy review workflow", "high"))
        if debt_prediction.get("direction") == "rising":
            actions.append(_action(project_id, "debt_reduction", "generate debt containment patch plan", "high"))
        if policy_trust.get("status") != "approved":
            actions.append(_action(project_id, "policy_alignment", "regenerate artifacts against policy DSL", "required"))
        if not actions:
            actions.append(_action(project_id, "continuous_scan", "keep repository intelligence scan active", "normal"))
        return {
            "mode": "autonomous_remediation",
            "project_id": project_id,
            "self_healing": True,
            "mutation_policy": "proposal_only_until_governance_approval",
            "actions": actions,
        }


class DeploymentAgentOrchestrator:
    def plan(
        self,
        *,
        project_id: str,
        environment: str,
        risk: dict[str, Any],
        trust_forecast: dict[str, Any],
    ) -> dict[str, Any]:
        risk_score = int(risk.get("risk_score", 0))
        forecast = int(trust_forecast.get("forecast_trust_score") or 0)
        agents = [
            _agent(project_id, environment, "preflight_agent", "validate policy and receipt chain"),
            _agent(project_id, environment, "deployment_agent", "execute governed deployment checklist"),
            _agent(project_id, environment, "assurance_agent", "observe deployment feedback and drift"),
        ]
        approved = risk_score < 75 and forecast >= 60
        return {
            "mode": "deployment_ai_agents",
            "project_id": project_id,
            "environment": environment,
            "approved_for_agent_execution": approved,
            "agents": agents,
        }


def _action(project_id: str, name: str, description: str, priority: str) -> dict[str, Any]:
    return {
        "action_id": "remediate-" + sha256(f"{project_id}:{name}:{description}:{priority}".encode()).hexdigest()[:12],
        "name": name,
        "description": description,
        "priority": priority,
        "status": "ready",
    }


def _agent(project_id: str, environment: str, name: str, mission: str) -> dict[str, Any]:
    return {
        "agent_id": "agent-" + sha256(f"{project_id}:{environment}:{name}:{mission}".encode()).hexdigest()[:12],
        "name": name,
        "mission": mission,
        "status": "planned",
    }


_DEFAULT_REMEDIATION_ENGINE = AutonomousRemediationEngine()
_DEFAULT_DEPLOYMENT_AGENTS = DeploymentAgentOrchestrator()


def get_autonomous_remediation_engine() -> AutonomousRemediationEngine:
    return _DEFAULT_REMEDIATION_ENGINE


def get_deployment_agent_orchestrator() -> DeploymentAgentOrchestrator:
    return _DEFAULT_DEPLOYMENT_AGENTS
