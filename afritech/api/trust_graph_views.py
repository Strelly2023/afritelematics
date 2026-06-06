from __future__ import annotations

from django.db import OperationalError, ProgrammingError
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from afritech.models import (
    ApprovalVote,
    GovernanceChangeRequest,
    GovernanceRule,
    GovernanceRuleVersion,
    ProofCertificate,
    RiskScore,
    RuleDependency,
)
from afritech.trust_graph import (
    explain_trust_query,
    list_trust_graph_records,
    process_trust_event,
)
from afritech.trust_graph.governance import (
    create_rule_version,
    register_vote,
    rollback_rule,
    submit_for_approval,
)
from afritech.trust_graph.impact_analysis import analyze_rule_change, detect_conflicts
from afritech.trust_graph.simulation import simulate


@api_view(["GET"])
def trust_graph_view(request) -> Response:
    return Response({"records": list_trust_graph_records()})


@api_view(["GET"])
def trust_history_view(request) -> Response:
    return Response({"records": list_trust_graph_records()})


@api_view(["GET"])
def trust_node_view(request, node_id: str) -> Response:
    for record in list_trust_graph_records(limit=100):
        if record["node_id"] == node_id:
            return Response(record)
    return Response({"detail": "node not found"}, status=404)


@api_view(["POST"])
def trust_process_view(request) -> Response:
    payload = request.data if isinstance(request.data, dict) else {}
    change = payload.get("change") if isinstance(payload.get("change"), dict) else payload
    node = process_trust_event(
        request=request,
        event_type=payload.get("type", "ManualTrustEvent"),
        actor_id=payload.get("actor_id", "operator"),
        subject_id=payload.get("subject_id", change.get("ride_id", "manual-event")),
        change=change,
        source=payload.get("source", "trust_api"),
    )
    return Response(
        {
            "node_id": node["node_id"],
            "proposal_id": node["proposal_id"],
            "decision": node["decision"]["status"],
            "execution": node["execution"]["status"],
            "risk": node["decision"].get("risk", {}),
            "proof": node["execution"].get("proof_certificate", {}),
        }
    )


@api_view(["POST"])
def trust_conversation_view(request) -> Response:
    query = request.data.get("query")
    if not isinstance(query, str) or not query.strip():
        return Response({"detail": "query is required"}, status=400)
    return Response(explain_trust_query(query.strip()))


@api_view(["POST"])
def trust_converse_view(request) -> Response:
    query = request.data.get("query")
    if not isinstance(query, str) or not query.strip():
        return Response({"detail": "query is required"}, status=400)
    return Response(explain_trust_query(query.strip()))


@api_view(["GET"])
def governance_rules_view(request) -> Response:
    try:
        rules = GovernanceRule.objects.select_related("active_version").all()
        return Response([_serialize_rule(rule) for rule in rules])
    except (OperationalError, ProgrammingError):
        return Response([])


@api_view(["POST"])
def governance_rule_save_view(request) -> Response:
    required = {"name", "condition_key", "expected_value"}
    if not required <= set(request.data):
        return Response({"detail": "name, condition_key, and expected_value are required"}, status=400)
    version = create_rule_version(
        request.data,
        user=request.data.get("user", "operator"),
    )
    if request.data.get("activate") is True:
        change = submit_for_approval(
            str(version.id),
            user=request.data.get("user", "operator"),
            required_approvals=1,
        )
        register_vote(str(change.id), request.data.get("reviewer", "admin"), "approve")
        version.refresh_from_db()

    return Response(
        {
            "version_id": str(version.id),
            "rule": version.rule.name,
            "version": version.version,
            "status": version.status,
        }
    )


@api_view(["POST"])
def governance_rule_submit_view(request, version_id: str) -> Response:
    change = submit_for_approval(
        version_id,
        user=request.data.get("user", "operator"),
        required_approvals=int(request.data.get("required_approvals", 2)),
    )
    return Response({"request_id": str(change.id), "status": change.status})


@api_view(["GET"])
def governance_pending_requests_view(request) -> Response:
    changes = GovernanceChangeRequest.objects.filter(status="pending").select_related(
        "rule_version__rule"
    )
    return Response(
        [
            {
                "id": str(change.id),
                "rule": change.rule_version.rule.name,
                "version": change.rule_version.version,
                "requested_by": change.requested_by,
                "required_approvals": change.required_approvals,
            }
            for change in changes
        ]
    )


@api_view(["POST"])
def governance_vote_view(request, request_id: str) -> Response:
    vote = request.data.get("vote")
    if vote not in {"approve", "reject"}:
        return Response({"detail": "vote must be approve or reject"}, status=400)
    result = register_vote(
        request_id,
        reviewer=request.data.get("reviewer", "admin"),
        vote=vote,
    )
    return Response(result)


@api_view(["GET"])
def governance_votes_view(request, request_id: str) -> Response:
    votes = ApprovalVote.objects.filter(change_request_id=request_id)
    return Response(
        [{"reviewer": vote.reviewer, "vote": vote.vote} for vote in votes]
    )


@api_view(["POST"])
def governance_rollback_view(request, rule_name: str) -> Response:
    return Response(rollback_rule(rule_name, request.data.get("reason", "manual")))


@api_view(["POST"])
def trust_simulate_view(request) -> Response:
    payload = request.data.get("payload", request.data)
    if not isinstance(payload, dict):
        return Response({"detail": "payload must be an object"}, status=400)
    return Response(
        simulate(
            payload,
            event_type=request.data.get("type", "ManualTrustEvent"),
            target_rule=request.data.get("target_rule"),
        )
    )


@api_view(["GET"])
def rule_graph_view(request) -> Response:
    graph = {}
    for dependency in RuleDependency.objects.select_related("from_rule", "to_rule"):
        graph.setdefault(
            dependency.from_rule.name,
            {"requires": [], "conflicts": [], "influences": []},
        )
        graph[dependency.from_rule.name][dependency.dependency_type].append(
            dependency.to_rule.name
        )
    return Response(graph)


@api_view(["POST"])
def rule_dependency_add_view(request) -> Response:
    from_rule = get_object_or_404(GovernanceRule, name=request.data.get("from"))
    to_rule = get_object_or_404(GovernanceRule, name=request.data.get("to"))
    dependency, _ = RuleDependency.objects.get_or_create(
        from_rule=from_rule,
        to_rule=to_rule,
        dependency_type=request.data.get("type", "influences"),
        defaults={"description": request.data.get("description", "")},
    )
    return Response({"id": str(dependency.id), "status": "created"})


@api_view(["GET"])
def rule_impact_view(request, rule_name: str) -> Response:
    return Response(
        {
            "impacted_rules": analyze_rule_change(rule_name),
            "conflicts": detect_conflicts(rule_name),
        }
    )


@api_view(["GET"])
def risk_scores_view(request) -> Response:
    scores = RiskScore.objects.order_by("-created_at")[:20]
    return Response(
        [
            {
                "scope": score.scope,
                "reference_id": score.reference_id,
                "score": score.score,
                "level": score.level,
                "breakdown": score.breakdown,
            }
            for score in scores
        ]
    )


@api_view(["GET"])
def proof_certificate_view(request, proposal_id: str) -> Response:
    certificate = get_object_or_404(ProofCertificate, proposal_id=proposal_id)
    return Response(
        {
            "proposal_id": certificate.proposal_id,
            "hash": certificate.proof_hash,
            "status": certificate.status,
            "invariants": certificate.invariants_proven,
            "proof_result": certificate.proof_result,
        }
    )


def _serialize_rule(rule: GovernanceRule) -> dict[str, object]:
    active = rule.active_version
    versions = GovernanceRuleVersion.objects.filter(rule=rule).order_by("-version")
    return {
        "id": str(rule.id),
        "name": rule.name,
        "active_version": _serialize_version(active) if active else None,
        "versions": [_serialize_version(version) for version in versions],
    }


def _serialize_version(version: GovernanceRuleVersion) -> dict[str, object]:
    return {
        "id": str(version.id),
        "version": version.version,
        "condition_key": version.condition_key,
        "expected_value": version.expected_value,
        "priority": version.priority,
        "description": version.description,
        "status": version.status,
    }
