from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgentFinding:
    agent: str
    risk: str
    severity: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {
            "agent": self.agent,
            "risk": self.risk,
            "severity": self.severity,
            "detail": self.detail,
        }


class BaseAgent:
    name = "base"

    def analyze(self, state: dict[str, Any]) -> AgentFinding | None:  # pragma: no cover - interface
        raise NotImplementedError


class PolicyAgent(BaseAgent):
    name = "policy"

    def analyze(self, state: dict[str, Any]) -> AgentFinding | None:
        if state.get("risk_score", 0) >= 60:
            return AgentFinding(
                agent=self.name,
                risk="POLICY_DRIFT",
                severity="high",
                detail="Predictive risk is high enough to require policy review before promotion.",
            )
        return None


class SecurityAgent(BaseAgent):
    name = "security"

    def analyze(self, state: dict[str, Any]) -> AgentFinding | None:
        scenarios = state.get("scenarios") if isinstance(state.get("scenarios"), list) else []
        for scenario in scenarios:
            if scenario.get("type") in {"direct_payment_call", "payment_bypass"}:
                return AgentFinding(
                    agent=self.name,
                    risk="SECURITY_RISK",
                    severity="critical",
                    detail="Payment authority bypass was detected in the simulated scenario set.",
                )
        return None


class TrustAgent(BaseAgent):
    name = "trust"

    def analyze(self, state: dict[str, Any]) -> AgentFinding | None:
        if int(state.get("predicted_risks") or 0) > 0:
            return AgentFinding(
                agent=self.name,
                risk="REPLAY_OR_TRUST_DRIFT",
                severity="high",
                detail="One or more predicted risks could affect replay or proof integrity.",
            )
        return None


class FinanceAgent(BaseAgent):
    name = "finance"

    def analyze(self, state: dict[str, Any]) -> AgentFinding | None:
        metrics = state.get("metrics") if isinstance(state.get("metrics"), dict) else {}
        if int(metrics.get("economic_pressure") or 0) >= 70:
            return AgentFinding(
                agent=self.name,
                risk="COST_OPTIMIZATION_REQUIRED",
                severity="medium",
                detail="Economic pressure is elevated and should be reviewed before scaling.",
            )
        return None


class OpsAgent(BaseAgent):
    name = "ops"

    def analyze(self, state: dict[str, Any]) -> AgentFinding | None:
        if int(state.get("prevented_violations") or 0) > 0:
            return AgentFinding(
                agent=self.name,
                risk="OPERATIONAL_PREVENTION_TRIGGERED",
                severity="medium",
                detail="Preventive actions were recommended for at least one scenario.",
            )
        return None


class AIAgent(BaseAgent):
    name = "ai"

    def analyze(self, state: dict[str, Any]) -> AgentFinding | None:
        if int(state.get("digital_twin", {}).get("twin_health_score", 0)) < 80:
            return AgentFinding(
                agent=self.name,
                risk="AI_GOVERNANCE_REVIEW",
                severity="medium",
                detail="Twin health is below the preferred threshold for unrestricted optimization.",
            )
        return None


class MultiAgentCoordinator:
    def __init__(self) -> None:
        self.agents: tuple[BaseAgent, ...] = (
            PolicyAgent(),
            SecurityAgent(),
            TrustAgent(),
            FinanceAgent(),
            OpsAgent(),
            AIAgent(),
        )

    def run(self, state: dict[str, Any]) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        for agent in self.agents:
            result = agent.analyze(state)
            if result is not None:
                findings.append(result.as_dict())
        return findings
