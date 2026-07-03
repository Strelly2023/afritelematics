from __future__ import annotations

from typing import Any


class SimulationEngine:
    def run(self, twin_state: dict[str, Any]) -> list[dict[str, Any]]:
        change = twin_state.get("change") if isinstance(twin_state.get("change"), dict) else {}
        scenario_type = str(change.get("type") or "steady_state")
        predictions: list[dict[str, Any]] = []

        if scenario_type == "steady_state":
            predictions.append(
                {
                    "scenario_id": "steady_state",
                    "risk": "NONE",
                    "severity": "low",
                    "preventive_action": "NONE",
                    "reason": "Current system state remains within governed bounds.",
                }
            )
            return predictions

        if scenario_type in {"remove_endpoint", "breaking_api_change"}:
            predictions.append(
                {
                    "scenario_id": scenario_type,
                    "risk": "API BREAKING CHANGE",
                    "severity": "high",
                    "preventive_action": "BLOCK_DEPLOYMENT",
                    "reason": "Contract removal would break versioned API compatibility.",
                }
            )

        if scenario_type in {"direct_payment_call", "payment_bypass"}:
            predictions.append(
                {
                    "scenario_id": scenario_type,
                    "risk": "PAYMENT AUTHORITY VIOLATION",
                    "severity": "critical",
                    "preventive_action": "REQUIRE_NOVAPOWER_APPROVAL",
                    "reason": "Payment execution must remain under NovaPower and NovaPay authority.",
                }
            )

        if scenario_type in {"missing_replay_verification", "replay_gap"}:
            predictions.append(
                {
                    "scenario_id": scenario_type,
                    "risk": "REPLAY INTEGRITY DRIFT",
                    "severity": "high",
                    "preventive_action": "ENABLE_REPLAY_GATE",
                    "reason": "Replay verification is required for authoritative execution.",
                }
            )

        if scenario_type in {"missing_policy_layer", "authority_bypass"}:
            predictions.append(
                {
                    "scenario_id": scenario_type,
                    "risk": "AUTHORITY BOUNDARY DRIFT",
                    "severity": "high",
                    "preventive_action": "REQUIRE_POLICY_CHECK",
                    "reason": "NovaPower policy enforcement must precede authoritative execution.",
                }
            )

        if not predictions:
            predictions.append(
                {
                    "scenario_id": scenario_type,
                    "risk": "LOW CONFIDENCE SCENARIO",
                    "severity": "low",
                    "preventive_action": "WATCH",
                    "reason": "Scenario is not recognized; manual review is preferred.",
                }
            )

        return predictions
