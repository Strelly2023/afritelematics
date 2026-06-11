from __future__ import annotations


def coordinate_agents(drift_reports: tuple[dict[str, object], ...]) -> dict[str, object]:
    if not drift_reports:
        return {
            "status": "no_drift",
            "confidence": 0.0,
            "reports": (),
            "activation_allowed": False,
            "runtime_mutation_allowed": False,
        }
    confidence = min(1.0, 0.6 + (0.1 * len(drift_reports)))
    return {
        "status": "drift_observed",
        "confidence": confidence,
        "reports": drift_reports,
        "proposal_required": True,
        "governance_required": True,
        "activation_allowed": False,
        "runtime_mutation_allowed": False,
        "rollback_execution_allowed": False,
    }


__all__ = ["coordinate_agents"]
