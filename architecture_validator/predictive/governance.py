from __future__ import annotations

from typing import Any

from architecture_validator.cli import run_checks
from architecture_validator.config import DEFAULT_CONFIG_PATH
from architecture_validator.predictive.autonomous import AutonomousCycle
from architecture_validator.predictive.digital_twin import DigitalTwin
from architecture_validator.predictive.predictive_engine import PredictiveEngine
from architecture_validator.remediation.self_heal import run_self_healing


def _compliance_payload(*, live: bool) -> dict[str, Any]:
    results = run_checks(DEFAULT_CONFIG_PATH if not live else DEFAULT_CONFIG_PATH)
    report = [result.as_dict() for result in results]
    passed = sum(1 for result in report if result.get("passed") is True)
    score = int(round((passed / len(report)) * 100)) if report else 0
    failed = [result for result in report if result.get("passed") is not True]
    return {
        "classification": "NOVARIDE_ARCHITECTURE_COMPLIANCE_REPORT",
        "status": "pass" if not failed else "fail",
        "score": score,
        "mode": "live_validator_scan" if live else "configured_control",
        "live_scan": live,
        "rules_total": len(report),
        "rules_passed": len(report) - len(failed),
        "rules_failed": len(failed),
        "report": report,
    }


def build_predictive_governance_payload(*, live: bool = False) -> dict[str, Any]:
    compliance = _compliance_payload(live=live)
    remediation = run_self_healing(apply=False)
    learning = remediation.get("learning") if isinstance(remediation.get("learning"), dict) else {}

    twin = DigitalTwin().load_system_state(
        compliance=compliance,
        remediation=remediation,
        learning=learning,
        live_context={"live": live},
    )

    scenarios = [
        {
            "scenario_id": "steady_state",
            "type": "steady_state",
            "description": "Mirror the current governed system state.",
        },
        {
            "scenario_id": "api_contract_drift",
            "type": "remove_endpoint",
            "description": "Remove a public endpoint and evaluate contract fallout.",
        },
        {
            "scenario_id": "authority_bypass",
            "type": "direct_payment_call",
            "description": "Attempt a direct payment execution path outside NovaPower.",
        },
        {
            "scenario_id": "replay_gap",
            "type": "missing_replay_verification",
            "description": "Skip replay verification in an authoritative flow.",
        },
    ]

    predictor = PredictiveEngine()
    scenario_results: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    preventive_actions: list[dict[str, Any]] = []
    predicted_risks = 0
    prevented_violations = 0

    for scenario in scenarios:
        simulated = twin.simulate_change(scenario)
        result = predictor.predict(simulated)
        scenario_results.append(
            {
                "scenario_id": scenario["scenario_id"],
                "type": scenario["type"],
                "description": scenario["description"],
                "risk_score": result["risk_score"],
                "predicted_risks": result["predicted_risks"],
                "prevented_violations": result["prevented_violations"],
                "predictions": result["predictions"],
                "preventive_actions": result["preventive_actions"],
            }
        )
        predictions.extend(result["predictions"])
        preventive_actions.extend(result["preventive_actions"])
        predicted_risks += int(result["predicted_risks"])
        prevented_violations += int(result["prevented_violations"])

    risk_score = max((scenario["risk_score"] for scenario in scenario_results), default=0)
    digital_twin = {
        "state": twin.state,
        "scenario_count": len(scenarios),
        "twin_health_score": twin.state.get("twin_health_score", 0),
        "mirrored_components": twin.state.get("mirrored_components", []),
    }

    return {
        "classification": "NOVARIDE_PREDICTIVE_GOVERNANCE_REPORT",
        "mode": "live_validator_scan" if live else "configured_control",
        "source": "validator",
        "authority_boundary": "predictive_governance_is_advisory_and_simulation_only",
        "digital_twin": digital_twin,
        "scenarios": scenario_results,
        "predictions": predictions,
        "preventive_actions": preventive_actions,
        "predicted_risks": predicted_risks,
        "prevented_violations": prevented_violations,
        "risk_score": risk_score,
        "metrics": {
            "predicted_risks": predicted_risks,
            "prevented_violations": prevented_violations,
            "scenario_count": len(scenarios),
            "twin_health_score": twin.state.get("twin_health_score", 0),
        },
        "compliance": compliance,
        "remediation": remediation,
        "learning": learning,
    }


def build_autonomous_governance_payload(*, live: bool = False) -> dict[str, Any]:
    predictive = build_predictive_governance_payload(live=live)
    cycle = AutonomousCycle().run(predictive)
    crisis_results = cycle["crisis"]
    critical_scenarios = cycle["crisis_summary"]["critical_scenarios"]
    economic = cycle["decision"]
    refactor = cycle["improvements"]

    return {
        "classification": "NOVARIDE_AUTONOMOUS_MULTI_AGENT_GOVERNANCE_REPORT",
        "mode": predictive.get("mode"),
        "source": predictive.get("source"),
        "authority_boundary": "multi_agent_governance_is_advisory_and_simulation_only",
        "digital_twin": predictive.get("digital_twin", {}),
        "multi_agent": {
            "findings": cycle["risks"],
            "agent_count": len(cycle["risks"]),
            "severity_breakdown": {
                "critical": sum(1 for item in cycle["risks"] if item.get("severity") == "critical"),
                "high": sum(1 for item in cycle["risks"] if item.get("severity") == "high"),
                "medium": sum(1 for item in cycle["risks"] if item.get("severity") == "medium"),
                "low": sum(1 for item in cycle["risks"] if item.get("severity") == "low"),
            },
        },
        "crisis": crisis_results,
        "crisis_summary": {
            "max_risk_score": cycle["crisis_summary"]["max_risk_score"],
            "critical_scenarios": critical_scenarios,
            "scenario_count": len(crisis_results),
            "black_swan": {
                "event": "GLOBAL_PAYMENT_FAILURE",
                "impact": "CRITICAL",
                "requires": "manual_intervention",
                "authority_boundary": "simulation_only",
            },
        },
        "economic_optimization": economic,
        "refactor_suggestions": refactor,
        "metrics": {
            "predicted_risks": predictive.get("predicted_risks", 0),
            "prevented_violations": predictive.get("prevented_violations", 0),
            "multi_agent_findings": len(cycle["risks"]),
            "critical_crisis_scenarios": len(critical_scenarios),
            "economic_efficiency": economic.get("cost_efficiency", 0),
            "refactor_suggestions_total": len(refactor),
            "twin_health_score": predictive.get("digital_twin", {}).get("twin_health_score", 0),
        },
        "predictive": predictive,
    }
