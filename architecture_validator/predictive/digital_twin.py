from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DigitalTwin:
    state: dict[str, Any] = field(default_factory=dict)

    def load_system_state(
        self,
        *,
        compliance: dict[str, Any],
        remediation: dict[str, Any],
        learning: dict[str, Any],
        live_context: dict[str, Any] | None = None,
    ) -> "DigitalTwin":
        learning_risk = learning.get("risk_profile") if isinstance(learning.get("risk_profile"), dict) else {}
        learning_total = int(learning_risk.get("total") or 0)
        learning_score = int(learning_risk.get("score") or (100 if learning_total == 0 else 0))
        compliance_score = int(compliance.get("score") or 0)
        remediation_score = 100 if remediation.get("final_passed") is True else 60
        twin_health_score = int(round((compliance_score * 0.55) + (learning_score * 0.25) + (remediation_score * 0.20)))
        self.state = {
            "compliance": compliance,
            "remediation": remediation,
            "learning": learning,
            "live_context": live_context or {},
            "compliance_score": compliance_score,
            "learning_score": learning_score,
            "remediation_score": remediation_score,
            "twin_health_score": max(0, min(100, twin_health_score)),
            "mirrored_components": [
                "architecture_spec",
                "api_contracts",
                "remediation_history",
                "learning_memory",
                "replay_evidence",
            ],
        }
        return self

    def simulate_change(self, change: dict[str, Any]) -> dict[str, Any]:
        simulated = dict(self.state)
        simulated["change"] = dict(change)
        simulated["simulation"] = {
            "scenario_id": str(change.get("scenario_id") or change.get("type") or "unknown"),
            "scenario_type": str(change.get("type") or "unknown"),
            "description": str(change.get("description") or "Predictive simulation"),
        }
        return simulated
