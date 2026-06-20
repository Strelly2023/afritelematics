"""Django REST surfaces for the NovaProgramming control plane."""

from __future__ import annotations

from typing import Any

from rest_framework.decorators import api_view
from rest_framework.response import Response

from afritech.afriprogramming.control_plane import get_control_plane


CONTROL_PLANE = get_control_plane()


@api_view(["GET"])
def novaprogramming_status(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.status(organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_catalog(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.catalog(organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_staff_roles(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    catalog = CONTROL_PLANE.catalog(organization_id=organization_id)
    return Response(
        {
            "platform": catalog["platform"],
            "roles": catalog["staff_roles"],
            "read_only": True,
        }
    )


@api_view(["GET"])
def novaprogramming_staff_dashboard(request, role: str) -> Response:
    project_id = str(request.query_params.get("project_id", "project-employee-rbac"))
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.staff_dashboard(role, project_id, organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_studio_context(request, project_id: str) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.studio_context(project_id, organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_studio_generate_code(request) -> Response:
    prompt = str(request.data.get("prompt", "")).strip()
    if not prompt:
        return Response({"detail": "prompt required"}, status=400)
    mode = str(request.data.get("mode", "code")).strip() or "code"
    project_id = str(request.data.get("project_id", "project-employee-rbac")).strip()
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.studio_generate(
            prompt=prompt,
            mode=mode,
            project_id=project_id,
            organization_id=organization_id,
            actor_user_id="django",
            actor_role="developer",
        )
    )


@api_view(["POST"])
def novaprogramming_studio_explain_code(request) -> Response:
    code = str(request.data.get("code", "")).strip()
    if not code:
        return Response({"detail": "code required"}, status=400)
    context = str(request.data.get("context", "")).strip()
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.studio_explain(
            code=code,
            context=context,
            organization_id=organization_id,
            actor_user_id="django",
            actor_role="developer",
        )
    )


@api_view(["POST"])
def novaprogramming_studio_analyze_repo(request) -> Response:
    project_id = str(request.data.get("project_id", "project-employee-rbac")).strip()
    focus = str(request.data.get("focus", "")).strip()
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.studio_analyze(
            project_id=project_id,
            focus=focus,
            organization_id=organization_id,
            actor_user_id="django",
            actor_role="architect",
        )
    )


@api_view(["GET"])
def novaprogramming_cloud_services(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.cloud_services(organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_cloud_health(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.cloud_health(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_cloud_request_deploy(request) -> Response:
    service = str(request.data.get("service", "")).strip()
    if not service:
        return Response({"detail": "service required"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.cloud_request_deploy(
            service=service,
            environment=str(request.data.get("environment", "staging")).strip() or "staging",
            image=str(request.data.get("image", "nova-programming:latest")).strip(),
            rationale=str(request.data.get("rationale", "")).strip(),
            organization_id=organization_id,
            requested_by="django",
            requested_role="operator",
        )
    )


@api_view(["POST"])
def novaprogramming_cloud_deploy(request) -> Response:
    request_id = str(request.data.get("request_id", "")).strip()
    if not request_id:
        return Response({"detail": "request_id required"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    try:
        return Response(
            CONTROL_PLANE.cloud_deploy(
                request_id=request_id,
                service=str(request.data.get("service", "")).strip() or "api",
                environment=str(request.data.get("environment", "staging")).strip() or "staging",
                image=str(request.data.get("image", "nova-programming:latest")).strip(),
                organization_id=organization_id,
                deployed_by="django",
                actor_role="devops",
            )
        )
    except PermissionError as exc:
        return Response({"detail": str(exc)}, status=403)


@api_view(["POST"])
def novaprogramming_cloud_scale(request) -> Response:
    service = str(request.data.get("service", "")).strip()
    if not service:
        return Response({"detail": "service required"}, status=400)
    try:
        replicas = int(request.data.get("replicas", 1))
    except (TypeError, ValueError):
        return Response({"detail": "replicas must be an integer"}, status=400)
    try:
        organization_id = str(request.data.get("organization_id", "")).strip() or None
        return Response(
            CONTROL_PLANE.cloud_scale(
                service=service,
                replicas=replicas,
                organization_id=organization_id,
                deployed_by="django",
                actor_role="devops",
            )
        )
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=400)


@api_view(["POST"])
def novaprogramming_governance_policy(request) -> Response:
    policy_name = str(request.data.get("policy_name", "")).strip()
    target = str(request.data.get("target", "")).strip()
    description = str(request.data.get("description", "")).strip()
    if not policy_name or not target:
        return Response({"detail": "policy_name and target required"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.governance_policy(
            policy_name=policy_name,
            target=target,
            description=description,
            organization_id=organization_id,
            actor_user_id="django",
            actor_role="manager",
        )
    )


@api_view(["GET"])
def novaprogramming_governance_audit_log(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.audit_log(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_governance_check(request) -> Response:
    policy_name = str(request.data.get("policy_name", "default-policy")).strip() or "default-policy"
    target = str(request.data.get("target", "")).strip()
    if not target:
        return Response({"detail": "target required"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.governance_check(
            policy_name=policy_name,
            target=target,
            organization_id=organization_id,
            actor_user_id="django",
            actor_role="verifier",
        )
    )


@api_view(["POST"])
def novaprogramming_governance_approve(request) -> Response:
    request_id = str(request.data.get("request_id", "")).strip()
    if not request_id:
        return Response({"detail": "request_id required"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.governance_approve(
            request_id=request_id,
            decision=str(request.data.get("decision", "approved")).strip() or "approved",
            notes=str(request.data.get("notes", "")).strip(),
            organization_id=organization_id,
            actor_user_id="django",
            actor_role="verifier",
        )
    )


@api_view(["POST"])
def novaprogramming_verify_generate_proof(request) -> Response:
    execution_id = str(request.data.get("execution_id", "")).strip()
    if not execution_id:
        return Response({"detail": "execution_id required"}, status=400)
    project_id = str(request.data.get("project_id", "project-employee-rbac")).strip()
    payload = request.data.get("payload", {})
    if not isinstance(payload, dict):
        return Response({"detail": "payload must be an object"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.verify_generate(
            execution_id=execution_id,
            project_id=project_id,
            payload=payload,
            organization_id=organization_id,
            actor_user_id="django",
            actor_role="verifier",
        )
    )


@api_view(["GET"])
def novaprogramming_verify_lookup(request, execution_id: str) -> Response:
    try:
        organization_id = str(request.query_params.get("organization_id", "")).strip() or None
        proof = CONTROL_PLANE.verify_lookup(execution_id)
        if organization_id and proof.get("organization_id") != organization_id:
            return Response({"detail": "proof not found"}, status=404)
        return Response(proof)
    except KeyError:
        return Response({"detail": "proof not found"}, status=404)


@api_view(["GET"])
def novaprogramming_verify_replay(request, execution_id: str) -> Response:
    try:
        organization_id = str(request.query_params.get("organization_id", "")).strip() or None
        replay = CONTROL_PLANE.verify_replay(
            execution_id,
            organization_id=organization_id,
            actor_user_id="django",
            actor_role="verifier",
        )
        if organization_id and replay.get("organization_id") != organization_id:
            return Response({"detail": "proof not found"}, status=404)
        return Response(replay)
    except KeyError:
        return Response({"detail": "proof not found"}, status=404)


@api_view(["GET"])
def novaprogramming_metrics(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.metrics(organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_trust(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.trust(organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_trust_stream(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    try:
        limit = int(request.query_params.get("limit", 100))
    except (TypeError, ValueError):
        limit = 100
    return Response(CONTROL_PLANE.trust_stream(organization_id=organization_id, limit=limit))


@api_view(["GET"])
def novaprogramming_trust_anomalies(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    try:
        limit = int(request.query_params.get("limit", 25))
    except (TypeError, ValueError):
        limit = 25
    return Response(CONTROL_PLANE.trust_anomalies(organization_id=organization_id, limit=limit))


@api_view(["POST"])
def novaprogramming_trust_verify_external(request) -> Response:
    payload = request.data if isinstance(request.data, dict) else {}
    required = ("organization_id", "proof_hash", "audit_hash", "receipt_hash")
    if any(not str(payload.get(field, "")).strip() for field in required):
        return Response({"detail": "organization_id, proof_hash, audit_hash and receipt_hash required"}, status=400)
    return Response(CONTROL_PLANE.trust_verify_external(payload))


@api_view(["GET"])
def novaprogramming_trust_risk(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.trust_risk(organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_trust_trends(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.trust_trends(organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_trust_replay(request, deployment_id: str) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    try:
        return Response(CONTROL_PLANE.trust_replay(deployment_id, organization_id=organization_id))
    except KeyError:
        return Response({"detail": "deployment not found"}, status=404)


@api_view(["GET"])
def novaprogramming_assurance(request, deployment_id: str) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    try:
        return Response(CONTROL_PLANE.assurance(deployment_id, organization_id=organization_id))
    except KeyError:
        return Response({"detail": "deployment not found"}, status=404)


@api_view(["GET"])
def novaprogramming_assurance_status(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.assurance_status(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_assurance_run(request) -> Response:
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    actor_user_id = str(request.data.get("actor_user_id", "django")).strip() or "django"
    return Response(CONTROL_PLANE.assurance_run(organization_id=organization_id, actor_user_id=actor_user_id))


@api_view(["GET"])
def novaprogramming_assurance_history(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    try:
        limit = int(request.query_params.get("limit", 100))
    except (TypeError, ValueError):
        limit = 100
    return Response(CONTROL_PLANE.assurance_history(organization_id=organization_id, limit=limit))


@api_view(["GET"])
def novaprogramming_assurance_alerts(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    try:
        limit = int(request.query_params.get("limit", 100))
    except (TypeError, ValueError):
        limit = 100
    return Response(CONTROL_PLANE.assurance_alerts(organization_id=organization_id, limit=limit))


@api_view(["GET"])
def novaprogramming_policy_registry(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.policy_registry(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_policy_create(request) -> Response:
    policy_name = str(request.data.get("policy_name", "")).strip()
    rule_type = str(request.data.get("rule_type", "")).strip()
    version = str(request.data.get("version", "v1")).strip() or "v1"
    rule_payload = request.data.get("rule_payload", {})
    if not policy_name or not rule_type or not isinstance(rule_payload, dict):
        return Response({"detail": "policy_name, rule_type and rule_payload required"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.policy_create(
            policy_name=policy_name,
            version=version,
            rule_type=rule_type,
            rule_payload=rule_payload,
            active=bool(request.data.get("active", True)),
            organization_id=organization_id,
            created_by="django",
        )
    )


@api_view(["POST"])
def novaprogramming_policy_evaluate(request) -> Response:
    action = str(request.data.get("action", "")).strip()
    target = str(request.data.get("target", "")).strip()
    payload = request.data.get("payload", {})
    if not action or not target or not isinstance(payload, dict):
        return Response({"detail": "action, target and payload required"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.policy_evaluate(
            action=action,
            target=target,
            payload=payload,
            organization_id=organization_id,
            actor_user_id="django",
        )
    )


@api_view(["GET"])
def novaprogramming_policy_decisions(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.policy_decisions(organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_retention(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.retention(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_retention_set(request) -> Response:
    record_type = str(request.data.get("record_type", "")).strip()
    if not record_type:
        return Response({"detail": "record_type required"}, status=400)
    try:
        retention_days = int(request.data.get("retention_days", 0))
    except (TypeError, ValueError):
        return Response({"detail": "retention_days must be an integer"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.retention_set(
            record_type=record_type,
            retention_days=retention_days,
            legal_hold=bool(request.data.get("legal_hold", True)),
            deletion_allowed=bool(request.data.get("deletion_allowed", False)),
            organization_id=organization_id,
        )
    )


@api_view(["GET"])
def novaprogramming_retention_check(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.retention_check(organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_reports_assurance(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.assurance_report(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_reports_assurance_generate(request) -> Response:
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    report_classification = str(request.data.get("report_classification", "INTERNAL_ASSURANCE_REPORT")).strip() or "INTERNAL_ASSURANCE_REPORT"
    return Response(
        CONTROL_PLANE.assurance_report_generate(
            organization_id=organization_id,
            report_classification=report_classification,
        )
    )


@api_view(["GET"])
def novaprogramming_trust_exchange_events(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    try:
        limit = int(request.query_params.get("limit", 100))
    except (TypeError, ValueError):
        limit = 100
    return Response(CONTROL_PLANE.trust_exchange_events(organization_id=organization_id, limit=limit))


@api_view(["POST"])
def novaprogramming_trust_exchange_verify(request) -> Response:
    payload = request.data if isinstance(request.data, dict) else {}
    organization_id = str(payload.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.trust_exchange_verify(receipt=payload, organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_certification(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.certification(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_certification_issue(request) -> Response:
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    certification_type = str(request.data.get("certification_type", "CONTROLLED_OPERATIONAL_STATE")).strip() or "CONTROLLED_OPERATIONAL_STATE"
    return Response(
        CONTROL_PLANE.certification_issue(
            organization_id=organization_id,
            certification_type=certification_type,
            actor_user_id="django",
        )
    )


@api_view(["POST"])
def novaprogramming_certification_verify(request) -> Response:
    certification = request.data.get("certification", {})
    if not isinstance(certification, dict):
        return Response({"detail": "certification must be an object"}, status=400)
    return Response(CONTROL_PLANE.certification_verify(certification))


@api_view(["GET"])
def novaprogramming_key_registry(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    key_family = str(request.query_params.get("key_family", "audit")).strip() or "audit"
    return Response(CONTROL_PLANE.key_registry(organization_id=organization_id, key_family=key_family))


@api_view(["POST"])
def novaprogramming_key_rotate(request) -> Response:
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.key_rotate(
            organization_id=organization_id,
            key_family=str(request.data.get("key_family", "audit")).strip() or "audit",
            rotated_by=str(request.data.get("rotated_by", "django")).strip() or "django",
            reason=str(request.data.get("reason", "rotation")).strip() or "rotation",
        )
    )


@api_view(["GET"])
def novaprogramming_signed_audit_chain(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.signed_audit_chain(organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_signed_audit_verify(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.signed_audit_verify(organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_distributed_trust_network(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    quorum = int(request.query_params.get("quorum", 2))
    return Response(CONTROL_PLANE.distributed_trust_network(organization_id=organization_id, quorum=quorum))


@api_view(["POST"])
def novaprogramming_federation_register(request) -> Response:
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.federation_register(
            peer_organization_id=str(request.data.get("peer_organization_id", "")).strip(),
            jurisdiction=str(request.data.get("jurisdiction", "")).strip(),
            role=str(request.data.get("role", "")).strip(),
            endpoint=str(request.data.get("endpoint", "")).strip(),
            public_key_id=str(request.data.get("public_key_id", "")).strip(),
            trust_level=str(request.data.get("trust_level", "TRUSTED")).strip() or "TRUSTED",
            organization_id=organization_id,
        )
    )


@api_view(["POST"])
def novaprogramming_federation_claim(request) -> Response:
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    payload = request.data.get("payload", {})
    if not isinstance(payload, dict):
        return Response({"detail": "payload must be an object"}, status=400)
    return Response(
        CONTROL_PLANE.federation_claim(
            peer_organization_id=str(request.data.get("peer_organization_id", "")).strip(),
            claim_type=str(request.data.get("claim_type", "")).strip(),
            payload=payload,
            organization_id=organization_id,
        )
    )


@api_view(["POST"])
def novaprogramming_federation_verify(request) -> Response:
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    claim = request.data.get("claim", {})
    if not isinstance(claim, dict):
        return Response({"detail": "claim must be an object"}, status=400)
    return Response(CONTROL_PLANE.federation_verify(claim=claim, organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_event_topics(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.event_topics(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_event_topic_create(request) -> Response:
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.event_topic_create(
            topic_name=str(request.data.get("topic_name", "")).strip(),
            description=str(request.data.get("description", "")).strip(),
            retention_days=int(request.data.get("retention_days", 0)),
            organization_id=organization_id,
        )
    )


@api_view(["POST"])
def novaprogramming_event_publish(request) -> Response:
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    payload = request.data.get("payload", {})
    headers = request.data.get("headers", {})
    if not isinstance(payload, dict) or not isinstance(headers, dict):
        return Response({"detail": "payload and headers must be objects"}, status=400)
    return Response(
        CONTROL_PLANE.event_publish(
            topic_name=str(request.data.get("topic_name", "")).strip(),
            event_type=str(request.data.get("event_type", "")).strip(),
            payload=payload,
            partition_key=str(request.data.get("partition_key", "")).strip(),
            headers=headers,
            organization_id=organization_id,
        )
    )


@api_view(["GET"])
def novaprogramming_event_consume(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    topic_name = str(request.query_params.get("topic_name", "")).strip() or None
    after_offset = int(request.query_params.get("after_offset", 0))
    limit = int(request.query_params.get("limit", 100))
    return Response(
        CONTROL_PLANE.event_consume(
            topic_name=topic_name,
            after_offset=after_offset,
            limit=limit,
            organization_id=organization_id,
        )
    )


@api_view(["POST"])
def novaprogramming_workflow_start(request) -> Response:
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    input_payload = request.data.get("input_payload", {})
    steps = request.data.get("steps")
    if not isinstance(input_payload, dict):
        return Response({"detail": "input_payload must be an object"}, status=400)
    if steps is not None and not isinstance(steps, list):
        return Response({"detail": "steps must be a list"}, status=400)
    return Response(
        CONTROL_PLANE.workflow_start(
            workflow_name=str(request.data.get("workflow_name", "")).strip(),
            input_payload=input_payload,
            steps=steps,
            organization_id=organization_id,
        )
    )


@api_view(["POST"])
def novaprogramming_workflow_signal(request) -> Response:
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    payload = request.data.get("payload", {})
    if not isinstance(payload, dict):
        return Response({"detail": "payload must be an object"}, status=400)
    return Response(
        CONTROL_PLANE.workflow_signal(
            workflow_id=str(request.data.get("workflow_id", "")).strip(),
            signal_name=str(request.data.get("signal_name", "")).strip(),
            payload=payload,
            organization_id=organization_id,
        )
    )


@api_view(["GET"])
def novaprogramming_workflow_status(request, workflow_id: str) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.workflow_status(workflow_id=workflow_id, organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_workflow_history(request, workflow_id: str) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.workflow_history(workflow_id=workflow_id, organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_zero_trust_policies(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.zero_trust_policies(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_zero_trust_policy_create(request) -> Response:
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    rule_payload = request.data.get("rule_payload", {})
    if not isinstance(rule_payload, dict):
        return Response({"detail": "rule_payload must be an object"}, status=400)
    return Response(
        CONTROL_PLANE.zero_trust_create(
            policy_name=str(request.data.get("policy_name", "")).strip(),
            version=str(request.data.get("version", "v1")).strip() or "v1",
            rule_type=str(request.data.get("rule_type", "")).strip(),
            rule_payload=rule_payload,
            active=bool(request.data.get("active", True)),
            organization_id=organization_id,
            created_by=str(request.data.get("created_by", "django")).strip() or "django",
        )
    )


@api_view(["POST"])
def novaprogramming_zero_trust_evaluate(request) -> Response:
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    context = request.data.get("context", {})
    if not isinstance(context, dict):
        return Response({"detail": "context must be an object"}, status=400)
    return Response(
        CONTROL_PLANE.zero_trust_evaluate(
            subject=str(request.data.get("subject", "")).strip(),
            action=str(request.data.get("action", "")).strip(),
            resource=str(request.data.get("resource", "")).strip(),
            context=context,
            organization_id=organization_id,
        )
    )


@api_view(["GET"])
def novaprogramming_zero_trust_decisions(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.zero_trust_decisions(organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_billing_summary(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.billing_summary(organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_insights(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.insights(organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_crypto_backends(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    key_family = str(request.query_params.get("key_family", "")).strip() or None
    return Response(CONTROL_PLANE.crypto_backends(organization_id=organization_id, key_family=key_family))


@api_view(["POST"])
def novaprogramming_crypto_backend_register(request) -> Response:
    backend_name = str(request.data.get("backend_name", "")).strip()
    provider_ref = str(request.data.get("provider_ref", "")).strip()
    if not backend_name or not provider_ref:
        return Response({"detail": "backend_name and provider_ref required"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.crypto_backend_register(
            backend_name=backend_name,
            provider_ref=provider_ref,
            key_family=str(request.data.get("key_family", "audit")).strip() or "audit",
            key_arn=str(request.data.get("key_arn", "")).strip() or None,
            hardware_bound=bool(request.data.get("hardware_bound", False)),
            organization_id=organization_id,
        )
    )


@api_view(["GET"])
def novaprogramming_certificate_chains(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.certificate_chains(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_certificate_issue(request) -> Response:
    subject = str(request.data.get("subject", "")).strip()
    if not subject:
        return Response({"detail": "subject required"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.certificate_issue(
            subject=subject,
            issuer=str(request.data.get("issuer", "NovaProgramming PKI")).strip() or "NovaProgramming PKI",
            key_family=str(request.data.get("key_family", "audit")).strip() or "audit",
            organization_id=organization_id,
        )
    )


@api_view(["POST"])
def novaprogramming_certificate_verify(request) -> Response:
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.certificate_verify(organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_stream_backends(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.stream_backends(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_stream_backend_register(request) -> Response:
    backend_name = str(request.data.get("backend_name", "")).strip()
    provider = str(request.data.get("provider", "")).strip()
    region = str(request.data.get("region", "")).strip()
    if not backend_name or not provider or not region:
        return Response({"detail": "backend_name, provider and region required"}, status=400)
    try:
        partitions = int(request.data.get("partitions", 1))
    except (TypeError, ValueError):
        return Response({"detail": "partitions must be an integer"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.stream_backend_register(
            backend_name=backend_name,
            provider=provider,
            region=region,
            partitions=partitions,
            organization_id=organization_id,
        )
    )


@api_view(["GET"])
def novaprogramming_trust_fabric_regions(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.trust_fabric_regions(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_trust_fabric_region_register(request) -> Response:
    region_name = str(request.data.get("region_name", "")).strip()
    country_code = str(request.data.get("country_code", "")).strip()
    provider = str(request.data.get("provider", "")).strip()
    if not region_name or not country_code or not provider:
        return Response({"detail": "region_name, country_code and provider required"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.trust_fabric_region_register(
            region_name=region_name,
            country_code=country_code,
            provider=provider,
            status=str(request.data.get("status", "active")).strip() or "active",
            organization_id=organization_id,
        )
    )


@api_view(["POST"])
def novaprogramming_trust_fabric_link(request) -> Response:
    source_region_id = str(request.data.get("source_region_id", "")).strip()
    target_region_id = str(request.data.get("target_region_id", "")).strip()
    if not source_region_id or not target_region_id:
        return Response({"detail": "source_region_id and target_region_id required"}, status=400)
    try:
        latency_ms = int(request.data.get("latency_ms", 0))
        trust_score = int(request.data.get("trust_score", 0))
    except (TypeError, ValueError):
        return Response({"detail": "latency_ms and trust_score must be integers"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.trust_fabric_link(
            source_region_id=source_region_id,
            target_region_id=target_region_id,
            latency_ms=latency_ms,
            trust_score=trust_score,
            status=str(request.data.get("status", "active")).strip() or "active",
            organization_id=organization_id,
        )
    )


@api_view(["GET"])
def novaprogramming_trust_fabric_graph(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.decentralized_trust_graph(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_trust_fabric_signed_request(request) -> Response:
    peer_organization_id = str(request.data.get("peer_organization_id", "")).strip()
    method = str(request.data.get("method", "POST")).strip() or "POST"
    url = str(request.data.get("url", "")).strip()
    if not peer_organization_id or not url:
        return Response({"detail": "peer_organization_id and url required"}, status=400)
    headers = request.data.get("headers", {})
    body = request.data.get("body", {})
    if headers and not isinstance(headers, dict):
        return Response({"detail": "headers must be an object"}, status=400)
    if body and not isinstance(body, dict):
        return Response({"detail": "body must be an object"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.trust_fabric_signed_request(
            peer_organization_id=peer_organization_id,
            method=method,
            url=url,
            headers=headers or {},
            body=body or {},
            organization_id=organization_id,
        )
    )


@api_view(["POST"])
def novaprogramming_trust_fabric_signed_request_verify(request) -> Response:
    envelope = request.data.get("envelope", {})
    if not isinstance(envelope, dict):
        return Response({"detail": "envelope must be an object"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.trust_fabric_signed_request_verify(
            envelope=envelope,
            organization_id=organization_id,
        )
    )


@api_view(["POST"])
def novaprogramming_identity_bind(request) -> Response:
    user_id = str(request.data.get("user_id", "")).strip()
    device_id = str(request.data.get("device_id", "")).strip()
    if not user_id or not device_id:
        return Response({"detail": "user_id and device_id required"}, status=400)
    try:
        human_trust_score = int(request.data.get("human_trust_score", 0))
        device_trust_score = int(request.data.get("device_trust_score", 0))
    except (TypeError, ValueError):
        return Response({"detail": "human_trust_score and device_trust_score must be integers"}, status=400)
    attestation = request.data.get("attestation", {})
    if not isinstance(attestation, dict):
        return Response({"detail": "attestation must be an object"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.identity_bind(
            user_id=user_id,
            device_id=device_id,
            human_trust_score=human_trust_score,
            device_trust_score=device_trust_score,
            attestation=attestation,
            organization_id=organization_id,
        )
    )


@api_view(["GET"])
def novaprogramming_identity_bindings(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.identity_bindings(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_risk_prediction(request) -> Response:
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    entity_type = str(request.data.get("entity_type", "organization")).strip() or "organization"
    entity_id = str(request.data.get("entity_id", "")).strip() or None
    try:
        horizon_days = int(request.data.get("horizon_days", 30))
    except (TypeError, ValueError):
        return Response({"detail": "horizon_days must be an integer"}, status=400)
    return Response(
        CONTROL_PLANE.risk_prediction(
            entity_type=entity_type,
            entity_id=entity_id,
            horizon_days=horizon_days,
            organization_id=organization_id,
        )
    )


@api_view(["GET"])
def novaprogramming_risk_predictions(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.risk_predictions(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_trust_negotiation(request) -> Response:
    peer_organization_id = str(request.data.get("peer_organization_id", "")).strip()
    proposed_terms = request.data.get("proposed_terms", {})
    if not peer_organization_id or not isinstance(proposed_terms, dict):
        return Response({"detail": "peer_organization_id and proposed_terms required"}, status=400)
    try:
        trust_offer = int(request.data.get("trust_offer", 0))
        trust_floor = int(request.data.get("trust_floor", 0))
    except (TypeError, ValueError):
        return Response({"detail": "trust_offer and trust_floor must be integers"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.trust_negotiation(
            peer_organization_id=peer_organization_id,
            proposed_terms=proposed_terms,
            trust_offer=trust_offer,
            trust_floor=trust_floor,
            organization_id=organization_id,
        )
    )


@api_view(["GET"])
def novaprogramming_trust_negotiations(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.trust_negotiations(organization_id=organization_id))


@api_view(["GET"])
def novaprogramming_v9_schema(request) -> Response:
    try:
        partition_count = int(request.query_params.get("partition_count", 4))
    except (TypeError, ValueError):
        partition_count = 4
    return Response(CONTROL_PLANE.v9_schema(partition_count=partition_count))


@api_view(["POST"])
def novaprogramming_v9_trust_consensus(request) -> Response:
    payload = request.data if isinstance(request.data, dict) else {}
    proposal = payload.get("proposal", {})
    if not isinstance(proposal, dict):
        return Response({"detail": "proposal required"}, status=400)
    peer_votes = payload.get("peer_votes")
    quorum = payload.get("quorum")
    try:
        quorum_value = int(quorum) if quorum is not None else None
    except (TypeError, ValueError):
        return Response({"detail": "quorum must be an integer"}, status=400)
    organization_id = str(payload.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.trust_consensus(
            organization_id=organization_id or "django",
            proposal=proposal,
            peer_votes=peer_votes if isinstance(peer_votes, list) else None,
            quorum=quorum_value,
        )
    )


@api_view(["POST"])
def novaprogramming_v9_certificate_transparency_append(request) -> Response:
    payload = request.data if isinstance(request.data, dict) else {}
    subject = str(payload.get("subject", "")).strip()
    if not subject:
        return Response({"detail": "subject required"}, status=400)
    organization_id = str(payload.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.certificate_transparency_append(
            organization_id=organization_id or "django",
            subject=subject,
            issuer=str(payload.get("issuer", "NovaProgramming PKI")),
            key_family=str(payload.get("key_family", "audit")),
            status=str(payload.get("status", "active")),
            certificate_payload=payload.get("certificate_payload") if isinstance(payload.get("certificate_payload"), dict) else None,
        )
    )


@api_view(["GET", "POST"])
def novaprogramming_v9_certificate_transparency(request) -> Response:
    if request.method == "GET":
        return novaprogramming_v9_certificate_transparency_log(request)
    return novaprogramming_v9_certificate_transparency_append(request)


@api_view(["GET"])
def novaprogramming_v9_certificate_transparency_log(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.certificate_transparency_log(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_v9_key_revocation(request) -> Response:
    payload = request.data if isinstance(request.data, dict) else {}
    key_id = str(payload.get("key_id", "")).strip()
    if not key_id:
        return Response({"detail": "key_id required"}, status=400)
    reason = str(payload.get("reason", "revocation")).strip() or "revocation"
    revoked_by = str(payload.get("revoked_by", "system")).strip() or "system"
    organization_id = str(payload.get("organization_id", "")).strip() or None
    return Response(
        CONTROL_PLANE.key_revocation(
            organization_id=organization_id or "django",
            key_id=key_id,
            reason=reason,
            revoked_by=revoked_by,
        )
    )


@api_view(["GET"])
def novaprogramming_v9_key_revocations(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.key_revocations(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_v9_trace_span(request) -> Response:
    payload = request.data if isinstance(request.data, dict) else {}
    organization_id = str(payload.get("organization_id", "")).strip() or None
    actor_user_id = str(payload.get("actor_user_id", "django")).strip() or "django"
    operation_name = str(payload.get("operation_name", "")).strip()
    endpoint = str(payload.get("endpoint", "")).strip()
    if not operation_name or not endpoint:
        return Response({"detail": "operation_name and endpoint required"}, status=400)
    try:
        latency_ms = int(payload.get("latency_ms", 0))
        status_code = int(payload.get("status_code", 200))
    except (TypeError, ValueError):
        return Response({"detail": "latency_ms and status_code must be integers"}, status=400)
    return Response(
        CONTROL_PLANE.trace_span(
            organization_id=organization_id or "django",
            actor_user_id=actor_user_id,
            operation_name=operation_name,
            endpoint=endpoint,
            latency_ms=latency_ms,
            status_code=status_code,
            policy_decision_id=payload.get("policy_decision_id"),
            proof_hash=payload.get("proof_hash"),
            deployment_id=payload.get("deployment_id"),
            parent_span_id=payload.get("parent_span_id"),
            attributes=payload.get("attributes") if isinstance(payload.get("attributes"), dict) else {},
        )
    )


@api_view(["GET", "POST"])
def novaprogramming_v9_traces(request) -> Response:
    if request.method == "GET":
        return novaprogramming_v9_trace_spans(request)
    return novaprogramming_v9_trace_span(request)


@api_view(["GET"])
def novaprogramming_v9_trace_spans(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.trace_spans(organization_id=organization_id))


@api_view(["POST"])
def novaprogramming_v9_assurance_scheduler_run(request) -> Response:
    payload = request.data if isinstance(request.data, dict) else {}
    organization_ids = payload.get("organization_ids")
    if organization_ids is not None and not isinstance(organization_ids, list):
        return Response({"detail": "organization_ids must be a list"}, status=400)
    return Response(CONTROL_PLANE.assurance_scheduler_run(organization_ids=organization_ids))


@api_view(["GET"])
def novaprogramming_v9_assurance_scheduler_history(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(CONTROL_PLANE.assurance_scheduler_history(organization_id=organization_id))


__all__ = [
    "novaprogramming_catalog",
    "novaprogramming_assurance",
    "novaprogramming_assurance_alerts",
    "novaprogramming_assurance_history",
    "novaprogramming_assurance_run",
    "novaprogramming_assurance_status",
    "novaprogramming_cloud_deploy",
    "novaprogramming_cloud_health",
    "novaprogramming_cloud_request_deploy",
    "novaprogramming_cloud_scale",
    "novaprogramming_cloud_services",
    "novaprogramming_billing_summary",
    "novaprogramming_certification_issue",
    "novaprogramming_certification",
    "novaprogramming_certification_verify",
    "novaprogramming_distributed_trust_network",
    "novaprogramming_event_consume",
    "novaprogramming_event_publish",
    "novaprogramming_event_topic_create",
    "novaprogramming_event_topics",
    "novaprogramming_federation_claim",
    "novaprogramming_federation_register",
    "novaprogramming_federation_verify",
    "novaprogramming_key_registry",
    "novaprogramming_key_rotate",
    "novaprogramming_governance_audit_log",
    "novaprogramming_governance_approve",
    "novaprogramming_governance_check",
    "novaprogramming_governance_policy",
    "novaprogramming_insights",
    "novaprogramming_metrics",
    "novaprogramming_policy_create",
    "novaprogramming_policy_decisions",
    "novaprogramming_policy_evaluate",
    "novaprogramming_policy_registry",
    "novaprogramming_reports_assurance",
    "novaprogramming_reports_assurance_generate",
    "novaprogramming_retention",
    "novaprogramming_retention_check",
    "novaprogramming_retention_set",
    "novaprogramming_signed_audit_chain",
    "novaprogramming_signed_audit_verify",
    "novaprogramming_staff_dashboard",
    "novaprogramming_staff_roles",
    "novaprogramming_status",
    "novaprogramming_studio_analyze_repo",
    "novaprogramming_studio_context",
    "novaprogramming_studio_explain_code",
    "novaprogramming_studio_generate_code",
    "novaprogramming_trust",
    "novaprogramming_trust_anomalies",
    "novaprogramming_v9_assurance_scheduler_history",
    "novaprogramming_v9_assurance_scheduler_run",
    "novaprogramming_v9_certificate_transparency",
    "novaprogramming_v9_certificate_transparency_append",
    "novaprogramming_v9_certificate_transparency_log",
    "novaprogramming_v9_key_revocation",
    "novaprogramming_v9_key_revocations",
    "novaprogramming_v9_schema",
    "novaprogramming_v9_traces",
    "novaprogramming_v9_trace_span",
    "novaprogramming_v9_trace_spans",
    "novaprogramming_v9_trust_consensus",
    "novaprogramming_trust_replay",
    "novaprogramming_trust_risk",
    "novaprogramming_trust_exchange_events",
    "novaprogramming_trust_exchange_verify",
    "novaprogramming_trust_trends",
    "novaprogramming_trust_stream",
    "novaprogramming_trust_verify_external",
    "novaprogramming_workflow_history",
    "novaprogramming_workflow_signal",
    "novaprogramming_workflow_start",
    "novaprogramming_workflow_status",
    "novaprogramming_zero_trust_decisions",
    "novaprogramming_zero_trust_evaluate",
    "novaprogramming_zero_trust_policies",
    "novaprogramming_zero_trust_policy_create",
    "novaprogramming_verify_generate_proof",
    "novaprogramming_verify_lookup",
    "novaprogramming_verify_replay",
]
