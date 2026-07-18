from __future__ import annotations

from afritech.novacodepro import NCP008ExecutionContext, NCP008OperationsService, NovaCodeProRepository


def _ctx(environment: str = "production") -> NCP008ExecutionContext:
    return NCP008ExecutionContext(
        actor_id="platform-operator",
        tenant_id="novatech",
        organization_id="novatech",
        workspace_id="workspace-ops",
        project_id="project-ops",
        request_id="req-ops",
        environment=environment,
        region="Australia",
        role="ADMIN",
        permissions=(
            "operations.read",
            "operations.workspace.read",
            "operations.environment.read",
            "operations.service.read",
            "operations.alert.read",
            "operations.alert.acknowledge",
            "operations.incident.read",
            "operations.incident.manage",
            "operations.timeline.write",
            "operations.action.request",
            "operations.action.approve",
            "operations.action.execute",
            "operations.action.verify",
            "operations.deployment.read",
            "operations.deployment.rollback",
            "operations.slo.read",
            "operations.recovery.read",
            "operations.recovery.manage",
            "operations.postmortem.read",
            "operations.postmortem.write",
        ),
        correlation_id="corr-ops",
        causation_id="cause-ops",
    )


def _service(tmp_path):
    repository = NovaCodeProRepository(tmp_path / "ncp008.sqlite3")
    return NCP008OperationsService(repository), repository


def test_ncp008_service_lifecycle_and_idempotency(tmp_path) -> None:
    service, repository = _service(tmp_path)
    ctx = _ctx()

    workspace = service.create_workspace({"name": "Operations Workspace", "environment_ids": [], "service_ids": [], "region_ids": []}, ctx, idempotency_key="workspace-1")
    assert workspace["name"] == "Operations Workspace"

    environment = service.create_environment({"code": "prod", "name": "Production", "type": "PRODUCTION", "region": "Australia", "status": "ACTIVE"}, ctx, idempotency_key="env-1")
    service_record = service.create_service({"name": "Payments API", "environment_id": environment["id"], "health_status": "HEALTHY", "readiness_status": "HEALTHY", "deployment_status": "ACTIVE", "criticality": "MISSION_CRITICAL", "dependencies": [], "endpoints": []}, ctx, idempotency_key="service-1")

    alert = service.create_alert({"title": "Latency spike", "description": "p95 latency above threshold", "severity": "CRITICAL", "environment_id": environment["id"], "service_id": service_record["id"]}, ctx, idempotency_key="alert-1")
    incident = service.alert_to_incident(alert["id"], {"title": "Production latency incident", "severity": "SEV1", "type": "PERFORMANCE"}, ctx, idempotency_key="incident-1")
    transitioned = service.transition_incident(incident["id"], "INVESTIGATING", ctx)
    assert transitioned["status"] == "INVESTIGATING"
    timeline_event = service.add_incident_timeline_event(incident["id"], {"event_type": "NOTE", "title": "Investigating", "description": "Checked ingress latency"}, ctx, idempotency_key="timeline-1")
    assert timeline_event["incident_id"] == incident["id"]

    action = service.create_action(
        {
            "action_type": "service_restart",
            "service_id": service_record["id"],
            "environment_id": environment["id"],
            "reason": "Routine restart",
            "requested_parameters": {"window": "now"},
        },
        ctx,
        idempotency_key="action-1",
    )
    action_dup = service.create_action(
        {
            "action_type": "service_restart",
            "service_id": service_record["id"],
            "environment_id": environment["id"],
            "reason": "Routine restart",
            "requested_parameters": {"window": "now"},
        },
        ctx,
        idempotency_key="action-1",
    )
    assert action["id"] == action_dup["id"]

    approval = service.request_action_approval(action["id"], ctx)
    approver_ctx = NCP008ExecutionContext(
        actor_id="operations-approver",
        tenant_id=ctx.tenant_id,
        organization_id=ctx.organization_id,
        workspace_id=ctx.workspace_id,
        project_id=ctx.project_id,
        request_id="req-ops-approver",
        environment=ctx.environment,
        region=ctx.region,
        role=ctx.role,
        permissions=ctx.permissions,
        correlation_id=ctx.correlation_id,
        causation_id=ctx.causation_id,
    )
    approved = service.approve_action(action["id"], {"reason": "Approved for controlled test"}, approver_ctx)
    assert approved["action"]["status"] == "approved"
    execution = service.execute_action(action["id"], ctx)
    assert execution["status"] == "SUCCEEDED"
    verified = service.verify_action(action["id"], ctx)
    assert verified["verification"]["status"] == "verified"

    slo = service.create_slo({"name": "Availability SLO", "service_id": service_record["id"], "environment_id": environment["id"], "objective_type": "AVAILABILITY", "target": 0.999, "window": "30d"}, ctx, idempotency_key="slo-1")
    slo_eval = service.evaluate_slo(slo["id"], ctx)
    assert slo_eval["measurement"]["compliance_status"] in {"ACTIVE", "BREACHED"}

    recovery_plan = service.create_recovery_plan({"name": "Payments recovery", "environment_id": environment["id"], "service_id": service_record["id"], "steps": ["Notify", "Restart"], "rollback_steps": ["Stop"], "required_approvals": ["operations.action.approve"], "validation_steps": ["Health check"]}, ctx, idempotency_key="recovery-1")
    validation = service.validate_recovery_plan(recovery_plan["id"], ctx)
    assert validation["validation"]["status"] == "valid"

    review = service.create_post_incident_review(incident["id"], {"summary": "Review", "owners": ["ops"], "due_dates": {"ops": "2026-08-01"}}, ctx, idempotency_key="review-1")
    published = service.publish_post_incident_review(review["id"], ctx)
    assert published["status"] == "PUBLISHED"

    overview = service.overview(ctx)
    assert overview["service_count"] >= 1
    assert overview["incident_count"] >= 1
    assert overview["action_count"] >= 1
    assert overview["slo_count"] >= 1

    cross_tenant_ctx = NCP008ExecutionContext(
        actor_id="platform-operator",
        tenant_id="other-tenant",
        organization_id="other-tenant",
        workspace_id="workspace-ops",
        project_id="project-ops",
        request_id="req-ops",
        environment="production",
        region="Australia",
        role="ADMIN",
        permissions=ctx.permissions,
        correlation_id="corr-ops",
        causation_id="cause-ops",
    )
    try:
        service.get_workspace(workspace["id"], cross_tenant_ctx)
    except Exception as exc:  # noqa: BLE001
        assert getattr(exc, "status_code", None) == 403
    else:  # pragma: no cover - defensive
        raise AssertionError("cross-tenant access should fail")


def test_ncp008_service_state_validation(tmp_path) -> None:
    service, _ = _service(tmp_path)
    ctx = _ctx()
    environment = service.create_environment({"code": "production", "name": "Production", "type": "PRODUCTION", "region": "Australia", "status": "ACTIVE"}, ctx, idempotency_key="env-2")
    service_record = service.create_service({"name": "Gateway", "environment_id": environment["id"], "health_status": "HEALTHY", "readiness_status": "HEALTHY", "deployment_status": "ACTIVE", "criticality": "STANDARD", "dependencies": [], "endpoints": []}, ctx, idempotency_key="service-2")
    incident = service.create_incident({"title": "Deployment issue", "summary": "", "severity": "SEV2", "type": "DEPLOYMENT", "environment_id": environment["id"], "affected_service_ids": [service_record["id"]]}, ctx, idempotency_key="incident-2")
    try:
        service.transition_incident(incident["id"], "CLOSED", ctx)
    except Exception as exc:  # noqa: BLE001
        assert getattr(exc, "code", "") == "NCP008_INVALID_TRANSITION"
    else:  # pragma: no cover - defensive
        raise AssertionError("invalid transition should fail")

    policy = service.evaluate_action({"action_type": "deployment_rollback", "environment_id": environment["id"], "service_id": service_record["id"], "requested_parameters": {}}, ctx)
    assert policy["risk_level"] in {"critical", "high"}
