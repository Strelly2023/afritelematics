from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _as_text(value: Any, default: str) -> str:
    text = str(value or "").strip()
    return text if text else default


def _score(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return max(min(int(value), 100), 0)
    try:
        return max(min(int(float(str(value))), 100), 0)
    except Exception:
        return default


def _state_view(label: str, status: str, detail: str, evidence: list[str] | None = None) -> dict[str, Any]:
    return {
        "label": label,
        "status": status,
        "detail": detail,
        "evidence": list(evidence or []),
    }


def build_eros_manifest() -> dict[str, Any]:
    return {
        "id": "eros",
        "name": "NovaDigitalTwin Enterprise Resilience Operating System",
        "version": "1.0",
        "generated_at": _now(),
        "positioning": "Governed operational intelligence, resilience, simulation, and recovery control plane.",
        "core_views": [
            "Observed State",
            "Desired State",
            "Predicted State",
            "Simulated State",
            "Approved State",
            "Recovered State",
        ],
        "identity_contract": {
            "required_fields": ["id", "type", "owner", "jurisdiction", "classification", "version"],
            "governance_fields": ["lifecycle_state", "trust_state", "controls", "evidence", "lineage"],
        },
        "relationship_model": {
            "types": [
                "DEPENDS_ON",
                "HOSTED_BY",
                "OPERATED_BY",
                "PROTECTED_BY",
                "GOVERNED_BY",
                "SUPPLIED_BY",
                "CONNECTED_TO",
                "IMPACTS",
                "REQUIRES",
                "RECOVERS_WITH",
                "REPLACES",
            ],
            "first_class": True,
        },
        "authority_levels": [
            {"level": 0, "mode": "Observe"},
            {"level": 1, "mode": "Recommend"},
            {"level": 2, "mode": "Prepare"},
            {"level": 3, "mode": "Execute with Approval"},
            {"level": 4, "mode": "Execute Pre-Approved"},
            {"level": 5, "mode": "Emergency Containment"},
        ],
        "resilience_scores": [
            "Twin Fidelity Score",
            "Dependency Confidence Score",
            "Simulation Confidence Score",
            "Recovery Confidence Score",
            "Enterprise Resilience Score",
        ],
        "runtime_services": [
            "Twin Registry",
            "Twin State",
            "Twin Graph",
            "Simulation Engine",
            "Recovery Orchestrator",
            "Evidence Ledger",
            "Replay Engine",
        ],
        "lifecycle": ["Draft", "Validated", "Approved", "Observed", "Simulated", "Recovered", "Retired"],
        "notes": [
            "The twin is the enterprise reality model.",
            "The resilience model is separate from operational state but connected to it.",
            "All high-risk interventions require policy evaluation and evidence capture.",
        ],
    }


def build_resilience_model() -> dict[str, Any]:
    return {
        "id": "nerm",
        "name": "NovaTech Enterprise Resilience Model",
        "version": "1.0",
        "generated_at": _now(),
        "objects": [
            "Dependency",
            "Recovery Plan",
            "Recovery Workflow",
            "Recovery Test",
            "Resilience Score",
            "Recovery Evidence",
            "Blast Radius",
            "Recovery Confidence",
            "RTO",
            "RPO",
        ],
        "scorecards": [
            "Availability",
            "Recovery Confidence",
            "Dependency Confidence",
            "Simulation Confidence",
            "Control Effectiveness",
            "Evidence Completeness",
        ],
        "lifecycle": ["Observe", "Assess", "Simulate", "Approve", "Execute", "Verify", "Learn"],
    }


def build_twin_identity(payload: dict[str, Any]) -> dict[str, Any]:
    twin_id = _as_text(payload.get("id"), _new_id("twin"))
    twin_type = _as_text(payload.get("type"), "SERVICE").upper()
    owner = _as_text(payload.get("owner"), "NovaTech")
    jurisdiction = _as_text(payload.get("jurisdiction"), "AU")
    classification = _as_text(payload.get("classification"), "INTERNAL").upper()
    version = int(payload.get("version") or 1)
    tenant_id = _as_text(payload.get("tenant_id"), "novatech")
    return {
        "id": twin_id,
        "type": twin_type,
        "name": _as_text(payload.get("name"), twin_id.replace("-", " ").title()),
        "owner": owner,
        "tenant_id": tenant_id,
        "jurisdiction": jurisdiction,
        "classification": classification,
        "version": version,
        "lifecycle_state": _as_text(payload.get("lifecycle_state"), "ACTIVE").upper(),
        "trust_state": _as_text(payload.get("trust_state"), "TRUSTED").upper(),
    }


def build_twin_relationship(payload: dict[str, Any]) -> dict[str, Any]:
    criticality = _as_text(payload.get("criticality"), "MEDIUM").upper()
    return {
        "id": _as_text(payload.get("id"), _new_id("relationship")),
        "source": _as_text(payload.get("source"), ""),
        "target": _as_text(payload.get("target"), ""),
        "type": _as_text(payload.get("type"), "DEPENDS_ON").upper(),
        "criticality": criticality,
        "weight": float(payload.get("weight") or 1.0),
        "rto": _as_text(payload.get("rto"), "15m"),
        "rpo": _as_text(payload.get("rpo"), "5m"),
        "recovery_difficulty": float(payload.get("recovery_difficulty") or 1.0),
        "confidence": min(max(float(payload.get("confidence") or 0.9), 0.0), 1.0),
        "evidence": list(payload.get("evidence") or []),
        "created_at": _now(),
    }


def build_twin_record(payload: dict[str, Any]) -> dict[str, Any]:
    identity = build_twin_identity(payload)
    observed_state = _state_view(
        "Observed State",
        _as_text(payload.get("observed_state"), "UNKNOWN").upper(),
        _as_text(payload.get("observed_detail"), "No live observation has been captured."),
        list(payload.get("observed_evidence") or []),
    )
    desired_state = _state_view(
        "Desired State",
        _as_text(payload.get("desired_state"), "AVAILABLE").upper(),
        _as_text(payload.get("desired_detail"), "Target operational posture."),
        list(payload.get("desired_evidence") or []),
    )
    predicted_state = _state_view(
        "Predicted State",
        _as_text(payload.get("predicted_state"), "UNKNOWN").upper(),
        _as_text(payload.get("predicted_detail"), "No prediction available."),
        list(payload.get("predicted_evidence") or []),
    )
    simulated_state = _state_view(
        "Simulated State",
        _as_text(payload.get("simulated_state"), "NOT_RUN").upper(),
        _as_text(payload.get("simulated_detail"), "No simulation has been executed."),
        list(payload.get("simulated_evidence") or []),
    )
    approved_state = _state_view(
        "Approved State",
        _as_text(payload.get("approved_state"), "PENDING").upper(),
        _as_text(payload.get("approved_detail"), "Awaiting governed approval."),
        list(payload.get("approved_evidence") or []),
    )
    recovered_state = _state_view(
        "Recovered State",
        _as_text(payload.get("recovered_state"), "NOT_RECOVERED").upper(),
        _as_text(payload.get("recovered_detail"), "Recovery has not been validated."),
        list(payload.get("recovered_evidence") or []),
    )
    relationships = [build_twin_relationship(item) for item in list(payload.get("relationships") or [])]
    metrics = dict(payload.get("metrics") or {})
    scores = dict(payload.get("scores") or {})
    twin = {
        **identity,
        "summary": _as_text(payload.get("summary"), "Enterprise digital twin record."),
        "status": _as_text(payload.get("status"), "healthy").lower(),
        "region": _as_text(payload.get("region"), "Australia"),
        "sources": list(payload.get("sources") or []),
        "controls": list(payload.get("controls") or []),
        "evidence": list(payload.get("evidence") or []),
        "lineage": list(payload.get("lineage") or []),
        "metrics": metrics,
        "state": {
            "observed": observed_state,
            "desired": desired_state,
            "predicted": predicted_state,
            "simulated": simulated_state,
            "approved": approved_state,
            "recovered": recovered_state,
        },
        "observed_state": observed_state["status"],
        "desired_state": desired_state["status"],
        "predicted_state": predicted_state["status"],
        "simulated_state": simulated_state["status"],
        "approved_state": approved_state["status"],
        "recovered_state": recovered_state["status"],
        "relationships": relationships,
        "resilience": {
            "twin_fidelity_score": int(scores.get("twin_fidelity_score") or 0),
            "dependency_confidence_score": int(scores.get("dependency_confidence_score") or 0),
            "simulation_confidence_score": int(scores.get("simulation_confidence_score") or 0),
            "recovery_confidence_score": int(scores.get("recovery_confidence_score") or 0),
            "enterprise_resilience_score": int(scores.get("enterprise_resilience_score") or 0),
        },
        "recovery": {
            "status": _as_text((payload.get("recovery") or {}).get("status"), "NOT_STARTED").upper()
            if isinstance(payload.get("recovery"), dict)
            else "NOT_STARTED",
            "plan_id": _as_text((payload.get("recovery") or {}).get("plan_id"), "") if isinstance(payload.get("recovery"), dict) else "",
            "workflow": dict((payload.get("recovery") or {}).get("workflow") or {}) if isinstance(payload.get("recovery"), dict) else {},
            "evidence_id": _as_text((payload.get("recovery") or {}).get("evidence_id"), "") if isinstance(payload.get("recovery"), dict) else "",
        },
        "created_at": _now(),
        "updated_at": _now(),
    }
    twin["scores"] = derive_resilience_scores(twin)
    twin["resilience"] = dict(twin["scores"])
    return twin


def derive_resilience_scores(twin: dict[str, Any]) -> dict[str, int]:
    relationships = list(twin.get("relationships") or [])
    evidence_count = len(list(twin.get("evidence") or []))
    source_count = len(list(twin.get("sources") or []))
    metrics = dict(twin.get("metrics") or {})
    risk_pressure = _score(metrics.get("risk_score") or metrics.get("risk") or 0)
    recovery_pressure = _score(metrics.get("mttr_minutes") or metrics.get("recovery_minutes") or 0)
    dependency_confidence = 70
    if relationships:
        dependency_confidence = int(sum(float(item.get("confidence") or 0.9) for item in relationships) / len(relationships) * 100)
    twin_fidelity = min(100, 65 + min(source_count * 5, 25) + min(evidence_count * 4, 12))
    simulation_confidence = int(twin.get("simulation_confidence") or max(60, 100 - recovery_pressure))
    recovery_confidence = int(twin.get("recovery_confidence") or max(60, 100 - recovery_pressure + evidence_count))
    enterprise_resilience = max(
        0,
        min(
            100,
            round(
                (twin_fidelity * 0.22)
                + (dependency_confidence * 0.24)
                + (simulation_confidence * 0.18)
                + (recovery_confidence * 0.26)
                + (100 - risk_pressure) * 0.10,
            ),
        ),
    )
    return {
        "twin_fidelity_score": int(twin_fidelity),
        "dependency_confidence_score": int(dependency_confidence),
        "simulation_confidence_score": int(simulation_confidence),
        "recovery_confidence_score": int(recovery_confidence),
        "enterprise_resilience_score": int(enterprise_resilience),
    }


def apply_observation(twin: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(twin)
    observed_status = _as_text(payload.get("observed_state"), updated.get("observed_state") or "UNKNOWN").upper()
    observed_detail = _as_text(payload.get("observed_detail"), "Live observation updated.")
    observed_evidence = list(payload.get("observed_evidence") or [])
    state = dict(updated.get("state") or {})
    state["observed"] = _state_view("Observed State", observed_status, observed_detail, observed_evidence)
    updated["state"] = state
    updated["observed_state"] = observed_status
    updated["status"] = str(payload.get("status") or updated.get("status") or "healthy").lower()
    if payload.get("desired_state") is not None:
        desired_status = _as_text(payload.get("desired_state"), updated.get("desired_state") or "AVAILABLE").upper()
        state["desired"] = _state_view(
            "Desired State",
            desired_status,
            _as_text(payload.get("desired_detail"), "Desired state updated."),
            list(payload.get("desired_evidence") or []),
        )
        updated["desired_state"] = desired_status
    if payload.get("predicted_state") is not None:
        predicted_status = _as_text(payload.get("predicted_state"), updated.get("predicted_state") or "UNKNOWN").upper()
        state["predicted"] = _state_view(
            "Predicted State",
            predicted_status,
            _as_text(payload.get("predicted_detail"), "Prediction updated."),
            list(payload.get("predicted_evidence") or []),
        )
        updated["predicted_state"] = predicted_status
    updated["metrics"] = dict(payload.get("metrics") or updated.get("metrics") or {})
    updated["scores"] = derive_resilience_scores(updated)
    updated["resilience"] = dict(updated["scores"])
    updated["updated_at"] = _now()
    return updated


def simulate_twin(twin: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    simulated = deepcopy(twin)
    scenario = _as_text(payload.get("scenario"), "UNKNOWN")
    root_failure = _as_text(payload.get("root_failure"), scenario)
    relationships = list(simulated.get("relationships") or [])
    impacted_relationships = [
        relation
        for relation in relationships
        if relation.get("type") == "DEPENDS_ON" or relation.get("criticality") in {"HIGH", "CRITICAL"}
    ]
    blast_radius = int(payload.get("blast_radius") or max(len(impacted_relationships), 1))
    affected_entities = [relation.get("target") for relation in impacted_relationships if relation.get("target")]
    risk_before = int(simulated.get("scores", {}).get("enterprise_resilience_score") or 0)
    risk_after = max(0, risk_before - min(blast_radius * 8, 45))
    recovery_minutes = int(payload.get("predicted_recovery_minutes") or max(5, blast_radius * 6))
    recovery_plan = build_recovery_plan(simulated, {
        "scenario": scenario,
        "root_failure": root_failure,
        "blast_radius": blast_radius,
        "predicted_recovery_minutes": recovery_minutes,
        "affected_entities": affected_entities,
    })
    simulated["state"]["simulated"] = _state_view(
        "Simulated State",
        "DEGRADED" if blast_radius < 4 else "CRITICAL",
        f"Scenario {scenario} impacts {blast_radius} dependent entities.",
        list(payload.get("simulated_evidence") or []),
    )
    simulated["simulated_state"] = simulated["state"]["simulated"]["status"]
    simulated["resilience"] = derive_resilience_scores({
        **simulated,
        "metrics": {
            **dict(simulated.get("metrics") or {}),
            "risk_score": risk_after,
            "recovery_minutes": recovery_minutes,
        },
    })
    simulated["scores"] = dict(simulated["resilience"])
    return {
        "id": _new_id("simulation"),
        "twin_id": simulated["id"],
        "scenario": scenario,
        "root_failure": root_failure,
        "blast_radius": blast_radius,
        "affected_entities": affected_entities,
        "risk_before": risk_before,
        "risk_after": risk_after,
        "predicted_recovery_minutes": recovery_minutes,
        "recommended_actions": list(payload.get("recommended_actions") or [
            "activate recovery workflow",
            "validate downstream dependencies",
            "capture evidence",
        ]),
        "required_approvals": list(payload.get("required_approvals") or (
            ["NovaPolicy", "NovaRisk", "NovaCompliance"] if blast_radius >= 3 else ["NovaPolicy"]
        )),
        "confidence": float(payload.get("confidence") or min(0.99, 0.7 + blast_radius * 0.04)),
        "simulated_twin": simulated,
        "created_at": _now(),
    }


def build_recovery_plan(twin: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    blast_radius = int(payload.get("blast_radius") or 1)
    scenario = _as_text(payload.get("scenario"), "UNKNOWN")
    workflow_id = _as_text(payload.get("workflow_id"), _new_id("recovery-plan"))
    expected_rto = _as_text(payload.get("expected_rto"), f"{max(2, blast_radius * 3)}m")
    expected_rpo = _as_text(payload.get("expected_rpo"), "5m")
    steps = list(payload.get("steps") or [
        "verify_failure",
        "activate_replica",
        "switch_traffic",
        "validate_health",
        "capture_evidence",
    ])
    return {
        "id": workflow_id,
        "twin_id": twin["id"],
        "scenario": scenario,
        "status": "READY",
        "expected_rto": expected_rto,
        "expected_rpo": expected_rpo,
        "steps": steps,
        "approvals_required": list(payload.get("approvals_required") or (
            ["NovaPolicy", "NovaRisk", "NovaCompliance"] if blast_radius >= 3 else ["NovaPolicy"]
        )),
        "created_at": _now(),
    }


def execute_recovery(twin: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(twin)
    recovery_plan = dict(payload.get("recovery_plan") or build_recovery_plan(updated, payload))
    evidence = dict(payload.get("evidence") or {})
    if not evidence:
        evidence = {
            "id": _new_id("evidence"),
            "type": "recovery_evidence",
            "twin_id": updated["id"],
            "status": "VERIFIED",
            "summary": _as_text(payload.get("summary"), "Recovery validated and recorded."),
            "validated_at": _now(),
        }
    updated["state"]["recovered"] = _state_view(
        "Recovered State",
        "HEALTHY",
        _as_text(payload.get("recovered_detail"), "Recovery has been validated."),
        [evidence["id"]],
    )
    updated["state"]["approved"] = _state_view(
        "Approved State",
        "APPROVED",
        _as_text(payload.get("approved_detail"), "Recovery action approved through governance."),
        list(payload.get("approved_evidence") or []),
    )
    updated["recovered_state"] = "HEALTHY"
    updated["approved_state"] = "APPROVED"
    updated["status"] = "healthy"
    updated["recovery"] = {
        "status": "VERIFIED",
        "plan_id": recovery_plan["id"],
        "workflow": recovery_plan,
        "evidence_id": evidence["id"],
    }
    updated["evidence"] = [evidence, *list(updated.get("evidence") or [])]
    updated["scores"] = derive_resilience_scores({
        **updated,
        "metrics": {
            **dict(updated.get("metrics") or {}),
            "risk_score": max(0, int(payload.get("risk_after") or 20)),
            "recovery_minutes": int(payload.get("predicted_recovery_minutes") or 5),
        },
    })
    updated["resilience"] = dict(updated["scores"])
    updated["updated_at"] = _now()
    return {
        "twin": updated,
        "recovery_plan": recovery_plan,
        "evidence": evidence,
        "status": "VERIFIED",
        "created_at": _now(),
    }
