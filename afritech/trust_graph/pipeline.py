from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from typing import Any

from django.db import IntegrityError, OperationalError, ProgrammingError
from django.utils import timezone

from afritech.models import TrustGraphRecord
from afritech.trust_graph.impact_analysis import analyze_rule_change
from afritech.trust_graph.predictive_engine import (
    predict_failure,
    store_prediction_signal,
)
from afritech.trust_graph.proof_engine import (
    generate_proof_certificate,
    store_proof_certificate,
)
from afritech.trust_graph.risk_engine import compute_risk, store_risk_score
from afritech.trust_graph.rules_engine import evaluate_rules
from afritech.trust_graph.validation_engine import validate_proposal


TRUST_HEADER_NAMES = (
    "X-AfriRide-Event-Id",
    "X-AfriRide-Device-Id",
    "X-AfriRide-App-Version",
    "X-AfriRide-Client-Timestamp",
    "X-AfriRide-Test-Mode",
)

_MEMORY_RECORDS: list[dict[str, Any]] = []


@dataclass(frozen=True)
class TrustGraphNode:
    node_id: str
    event_id: str
    proposal_id: str
    source: str
    action: str
    actor_id: str
    subject_id: str
    request_headers: dict[str, Any]
    proposal: dict[str, Any]
    validation: dict[str, Any]
    decision: dict[str, Any]
    execution: dict[str, Any]
    linked_to: list[str]
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "event_id": self.event_id,
            "proposal_id": self.proposal_id,
            "source": self.source,
            "action": self.action,
            "actor_id": self.actor_id,
            "subject_id": self.subject_id,
            "request_headers": self.request_headers,
            "proposal": self.proposal,
            "validation": self.validation,
            "decision": self.decision,
            "execution": self.execution,
            "linked_to": self.linked_to,
            "created_at": self.created_at,
        }


def process_trust_event(
    *,
    request: Any,
    event_type: str,
    actor_id: str,
    subject_id: str,
    change: dict[str, Any],
    source: str = "driver_api",
    execution_status: str = "applied",
) -> dict[str, Any]:
    headers = extract_trust_headers(request)
    action = f"{request.method} {request.path}"
    event_id = headers.get("X-AfriRide-Event-Id") or f"evt-{uuid.uuid4().hex[:12]}"
    proposal_id = _stable_id("prop", event_id, event_type, subject_id)
    previous_node = _latest_record()

    proposal = {
        "proposal_id": proposal_id,
        "event_id": event_id,
        "type": event_type,
        "change": change,
        "source": source,
    }
    validation_data = validate_proposal(proposal)
    validation = {
        "passed": validation_data["passed"],
        "replay": "PASS" if validation_data["passed"] else "FAIL",
        "contracts": "PASS" if validation_data["passed"] else "FAIL",
        "risk": validation_data["risk"],
        "details": validation_data["details"],
        "evidence": _validation_evidence(validation_data),
    }
    decision_data = evaluate_rules(proposal, validation_data)
    impacted_rules = _impacted_rules(decision_data)
    risk = compute_risk(proposal, validation_data, decision_data, impacted_rules)
    store_risk_score(proposal_id, risk)
    prediction = predict_failure(proposal, validation_data, decision_data, risk)
    store_prediction_signal(proposal_id, prediction)

    decision_status = "approved" if decision_data["approved"] else "rejected"
    decision = {
        "status": decision_status,
        "approved_by": "system",
        "rules": decision_data["rules"],
        "rules_applied": [
            rule["rule"] for rule in decision_data["rules"] if rule.get("passed")
        ]
        or _rules_for_event(event_type),
        "failed_rules": [
            rule["rule"] for rule in decision_data["rules"] if not rule.get("passed")
        ],
        "risk": risk,
        "prediction": prediction,
    }
    final_execution_status = execution_status
    if decision_status != "approved":
        final_execution_status = "blocked"
    if prediction["will_fail"]:
        final_execution_status = "blocked_predicted_failure"

    execution = {
        "status": final_execution_status,
        "timestamp": timezone.now().isoformat(),
        "rollback_ready": True,
    }
    certificate = generate_proof_certificate(
        proposal,
        validation_data,
        decision,
        execution,
        risk,
    )
    store_proof_certificate(proposal_id, certificate)
    execution["proof_certificate"] = {
        "status": certificate["status"],
        "proof_hash": certificate["proof_hash"],
    }
    linked_to = [previous_node["node_id"]] if previous_node else []
    node_id = _stable_id("node", event_id, proposal_id, execution["timestamp"])

    node = TrustGraphNode(
        node_id=node_id,
        event_id=event_id,
        proposal_id=proposal_id,
        source=source,
        action=action,
        actor_id=actor_id,
        subject_id=subject_id,
        request_headers=headers,
        proposal=proposal,
        validation=validation,
        decision=decision,
        execution=execution,
        linked_to=linked_to,
        created_at=execution["timestamp"],
    )
    return _store_record(node)


def extract_trust_headers(request: Any) -> dict[str, Any]:
    return {
        header: request.headers.get(header)
        for header in TRUST_HEADER_NAMES
        if request.headers.get(header)
    }


def list_trust_graph_records(limit: int = 20) -> list[dict[str, Any]]:
    try:
        records = TrustGraphRecord.objects.all()[:limit]
        if records:
            return [_serialize_model(record) for record in records]
    except (OperationalError, ProgrammingError):
        pass
    return list(reversed(_MEMORY_RECORDS[-limit:]))


def explain_trust_query(query: str) -> dict[str, Any]:
    records = list_trust_graph_records(limit=20)
    node = records[0] if records else _seed_node()
    normalized = query.lower()
    tokens = set(re.findall(r"[a-z0-9_]+", normalized))

    if "safe" in normalized or "validation" in normalized:
        answer = _validation_answer(node)
    elif {"prove", "proof", "audit"} & tokens:
        answer = _proof_answer(node)
    elif "history" in normalized or "before" in normalized or "happened" in normalized:
        answer = _history_answer(node, records)
    elif "risk" in normalized or "fail" in normalized:
        answer = _risk_answer(node)
    elif "reject" in normalized or "simulate" in normalized:
        answer = _simulation_answer(node)
    else:
        answer = _decision_answer(node)

    return {
        "answer": answer,
        "evidence": {
            "node_id": node["node_id"],
            "event_id": node["event_id"],
            "proposal_id": node["proposal_id"],
            "decision": node["decision"],
            "validation": node["validation"],
            "execution": node["execution"],
            "risk": node["decision"].get("risk", {}),
            "prediction": node["decision"].get("prediction", {}),
        },
    }


def _store_record(node: TrustGraphNode) -> dict[str, Any]:
    payload = node.as_dict()
    try:
        record = TrustGraphRecord.objects.create(
            **{**payload, "created_at": timezone.now()}
        )
        return _serialize_model(record)
    except (IntegrityError, OperationalError, ProgrammingError):
        _MEMORY_RECORDS.append(payload)
        return payload


def _latest_record() -> dict[str, Any] | None:
    try:
        record = TrustGraphRecord.objects.first()
        if record is not None:
            return _serialize_model(record)
    except (OperationalError, ProgrammingError):
        pass
    return _MEMORY_RECORDS[-1] if _MEMORY_RECORDS else None


def _serialize_model(record: TrustGraphRecord) -> dict[str, Any]:
    return {
        "node_id": record.node_id,
        "event_id": record.event_id,
        "proposal_id": record.proposal_id,
        "source": record.source,
        "action": record.action,
        "actor_id": record.actor_id,
        "subject_id": record.subject_id,
        "request_headers": record.request_headers,
        "proposal": record.proposal,
        "validation": record.validation,
        "decision": record.decision,
        "execution": record.execution,
        "linked_to": record.linked_to,
        "created_at": (
            record.created_at.isoformat()
            if hasattr(record.created_at, "isoformat")
            else str(record.created_at)
        ),
    }


def _rules_for_event(event_type: str) -> list[str]:
    if event_type == "RideAccepted":
        return ["driver_available", "ride_pending", "validation_passed"]
    if event_type == "TripStarted":
        return ["ride_accepted", "driver_authorized", "validation_passed"]
    if event_type == "TripCompleted":
        return ["ride_started", "rollback_ready", "evidence_recorded"]
    if event_type == "DriverAvailabilityChanged":
        return ["driver_identity_present", "status_allowed", "event_recorded"]
    return ["request_valid", "validation_passed", "rollback_ready"]


def _validation_evidence(validation_data: dict[str, Any]) -> list[str]:
    evidence = [
        "request carried trust metadata",
        "rollback path remains available",
    ]
    passed_checks = [
        item["check"] for item in validation_data["details"] if item.get("passed")
    ]
    failed_checks = [
        item["check"] for item in validation_data["details"] if not item.get("passed")
    ]
    if passed_checks:
        evidence.append(f"passed checks: {', '.join(passed_checks)}")
    if failed_checks:
        evidence.append(f"failed checks: {', '.join(failed_checks)}")
    return evidence


def _impacted_rules(decision_data: dict[str, Any]) -> list[str]:
    impacted: list[str] = []
    for rule in decision_data.get("rules", []):
        impacted.extend(analyze_rule_change(rule["rule"]))
    return sorted(set(impacted))


def _decision_answer(node: dict[str, Any]) -> str:
    rules = ", ".join(node["decision"].get("rules_applied", []))
    return (
        f"Proposal {node['proposal_id']} was {node['decision']['status']} because "
        f"validation passed and these governance rules applied: {rules}."
    )


def _validation_answer(node: dict[str, Any]) -> str:
    validation = node["validation"]
    return (
        f"Proposal {node['proposal_id']} is safe under the current evidence: "
        f"replay={validation['replay']}, contracts={validation['contracts']}, "
        f"risk={validation['risk']}."
    )


def _history_answer(node: dict[str, Any], records: list[dict[str, Any]]) -> str:
    if len(records) < 2:
        return (
            f"Proposal {node['proposal_id']} is the first available trust graph record. "
            "No previous node is linked yet."
        )
    previous = records[1]
    return (
        f"Before {node['proposal_id']}, the system recorded {previous['proposal_id']} "
        f"for {previous['action']} with decision={previous['decision']['status']}."
    )


def _risk_answer(node: dict[str, Any]) -> str:
    risk = node["decision"].get("risk", {})
    prediction = node["decision"].get("prediction", {})
    if risk:
        return (
            f"The recorded risk for {node['proposal_id']} is {risk.get('level')} "
            f"({risk.get('score')} points). Prediction confidence is "
            f"{prediction.get('confidence', 0):.2f}; factors={prediction.get('factors', [])}."
        )
    return (
        f"The recorded risk for {node['proposal_id']} is {node['validation']['risk']}. "
        "The main control is rollback readiness, which is currently "
        f"{node['execution']['rollback_ready']}."
    )


def _simulation_answer(node: dict[str, Any]) -> str:
    return (
        f"If {node['proposal_id']} were rejected, execution would remain unapplied, "
        "the current system state would be preserved, and the trust graph would record "
        "a rejected decision node instead of an applied execution node."
    )


def _proof_answer(node: dict[str, Any]) -> str:
    certificate = node["execution"].get("proof_certificate") or {}
    if not certificate:
        return (
            f"Proposal {node['proposal_id']} has no persisted proof certificate yet, "
            "but its trust graph record still contains validation, decision, and execution evidence."
        )
    return (
        f"Proposal {node['proposal_id']} has a {certificate['status']} proof certificate. "
        f"Hash: {certificate['proof_hash']}. The hash binds proposal, validation, "
        "decision, execution, and risk evidence for later audit."
    )


def _seed_node() -> dict[str, Any]:
    timestamp = timezone.now().isoformat()
    return {
        "node_id": "node-demo-seed",
        "event_id": "evt-demo-seed",
        "proposal_id": "prop-demo-seed",
        "source": "demo",
        "action": "GET /system/evidence",
        "actor_id": "operator",
        "subject_id": "trust-surface",
        "request_headers": {},
        "proposal": {
            "proposal_id": "prop-demo-seed",
            "event_id": "evt-demo-seed",
            "type": "TrustSurfaceRead",
            "change": {"surface": "dashboard"},
            "source": "demo",
        },
        "validation": {"replay": "PASS", "contracts": "PASS", "risk": "LOW"},
        "decision": {
            "status": "approved",
            "approved_by": "system",
            "rules_applied": ["read_only", "evidence_available"],
        },
        "execution": {"status": "observed", "timestamp": timestamp, "rollback_ready": True},
        "linked_to": [],
        "created_at": timestamp,
    }


def _stable_id(prefix: str, *parts: str) -> str:
    raw = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest or uuid.uuid4().hex[:12]}"
