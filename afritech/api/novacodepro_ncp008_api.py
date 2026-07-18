from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response

from afritech.api.auth.jwt_device_auth import JWTClaims, get_current_claims
from afritech.novacodepro import NCP008Error, NCP008OperationsService, NovaCodeProPlatform, build_ncp008_context


ADMIN_ROLES = {
    "ADMIN",
    "PLATFORM_ADMIN",
    "PLATFORM_OWNER",
    "SUPER_ADMIN",
    "SYSTEM_ADMIN",
    "OPERATOR",
    "DEVOPS_ENGINEER",
    "SRE",
    "INCIDENT_COMMANDER",
    "SECURITY_ENGINEER",
    "COMPLIANCE_OFFICER",
}

READ_PERMISSIONS = {
    "operations.read",
    "operations.workspace.read",
    "operations.environment.read",
    "operations.service.read",
    "operations.observability.read",
    "operations.alert.read",
    "operations.incident.read",
    "operations.deployment.read",
    "operations.slo.read",
    "operations.recovery.read",
    "operations.postmortem.read",
    "operations.evidence.read",
    "operations.audit.read",
}

WRITE_PERMISSIONS = {
    "operations.action.request",
    "operations.action.approve",
    "operations.action.execute",
    "operations.action.verify",
    "operations.incident.declare",
    "operations.incident.manage",
    "operations.timeline.write",
    "operations.deployment.rollback",
    "operations.recovery.manage",
    "operations.postmortem.write",
}


def _handle(error: NCP008Error) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={
            "code": error.code,
            "message": error.message,
            "details": error.details,
        },
    ) from error


def _service(platform: NovaCodeProPlatform) -> NCP008OperationsService:
    return NCP008OperationsService(platform.repository)


def _require_permissions(*permissions: str) -> Callable[..., JWTClaims]:
    required = {permission for permission in permissions if permission}

    def dependency(claims: JWTClaims = Depends(get_current_claims)) -> JWTClaims:
        if claims.role in ADMIN_ROLES:
            return claims
        if not required:
            return claims
        allowed = set(str(permission) for permission in (claims.permissions or ()))
        if any(permission in allowed for permission in required):
            return claims
        raise HTTPException(status_code=403, detail={"code": "OPERATIONS_FORBIDDEN", "message": "Insufficient operations permission"})

    return dependency


def _ctx(claims: JWTClaims, request: Request, *, workspace_id: str | None = None, project_id: str | None = None, environment: str | None = None, region: str | None = None) -> Any:
    return build_ncp008_context(
        claims,
        workspace_id=workspace_id,
        project_id=project_id,
        request_id=request.headers.get("x-request-id") or request.headers.get("x-correlation-id") or None,
        environment=environment or request.headers.get("x-environment") or "development",
        region=region or request.headers.get("x-region") or "Australia",
    )


def _paginate_list(items: list[dict[str, Any]], *, limit: int, offset: int) -> list[dict[str, Any]]:
    return items[max(offset, 0) : max(offset, 0) + max(limit, 0)]


def _collection_crud(
    router: APIRouter,
    *,
    service: NCP008OperationsService,
    base_path: str,
    kind: str,
    list_key: str,
    singular_key: str,
    read_permission: str = "operations.read",
    write_permission: str = "operations.action.request",
    status_field: str = "status",
) -> None:
    @router.get(base_path, name=f"{kind}_list")
    def list_items(
        limit: int = Query(default=100, ge=1, le=1000),
        offset: int = Query(default=0, ge=0),
        claims: JWTClaims = Depends(_require_permissions(read_permission)),
        request: Request = None,
    ) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))  # pragma: no cover - request is always provided
        return {list_key: _paginate_list(service.list_collection(kind, ctx), limit=limit, offset=offset), "count": len(service.list_collection(kind, ctx))}

    @router.post(base_path, name=f"{kind}_create")
    def create_item(
        payload: dict[str, Any],
        claims: JWTClaims = Depends(_require_permissions(write_permission)),
        request: Request = None,
        x_idempotency_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        return service.create_collection_item(kind, payload, ctx, idempotency_key=x_idempotency_key or str(payload.get("idempotency_key") or ""), status=payload.get(status_field))

    @router.get(f"{base_path}" + "/{item_id}", name=f"{kind}_get")
    def get_item(item_id: str, claims: JWTClaims = Depends(_require_permissions(read_permission)), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        return {singular_key: service.get_collection_item(kind, item_id, ctx)}

    @router.patch(f"{base_path}" + "/{item_id}", name=f"{kind}_update")
    def update_item(item_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(_require_permissions(write_permission)), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        return service.update_collection_item(kind, item_id, payload, ctx, status=payload.get(status_field))


def build_novacodepro_ncp008_router(platform: NovaCodeProPlatform) -> APIRouter:
    service = _service(platform)
    router = APIRouter(prefix="/api/v1/operations", tags=["novacodepro-operations"])

    def read_claims(claims: JWTClaims = Depends(_require_permissions("operations.read"))) -> JWTClaims:
        return claims

    def write_claims(claims: JWTClaims = Depends(_require_permissions(*WRITE_PERMISSIONS))) -> JWTClaims:
        return claims

    @router.get("/overview", name="ncp008_overview")
    def overview(claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.overview(_ctx(claims, request or Request({"type": "http"})))

    @router.get("/activity", name="ncp008_activity")
    def activity(claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"activity": service.activity(_ctx(claims, request or Request({"type": "http"})))}

    @router.get("/risk", name="ncp008_risk")
    def risk(claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.risk(_ctx(claims, request or Request({"type": "http"})))

    @router.get("/readiness", name="ncp008_readiness")
    def readiness(claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.readiness(_ctx(claims, request or Request({"type": "http"})))

    # Workspaces
    @router.get("/workspaces", name="ncp008_workspaces_list")
    def list_workspaces(limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        items = service.list_workspaces(ctx)
        return {"workspaces": _paginate_list(items, limit=limit, offset=offset), "count": len(items)}

    @router.post("/workspaces", name="ncp008_workspaces_create")
    def create_workspace(payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None, x_idempotency_key: str | None = Header(default=None)) -> dict[str, Any]:
        return service.create_workspace(payload, _ctx(claims, request or Request({"type": "http"})), idempotency_key=x_idempotency_key or str(payload.get("idempotency_key") or ""))

    @router.get("/workspaces/{workspace_id}", name="ncp008_workspaces_get")
    def get_workspace(workspace_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"workspace": service.get_workspace(workspace_id, _ctx(claims, request or Request({"type": "http"})))}

    @router.patch("/workspaces/{workspace_id}", name="ncp008_workspaces_update")
    def update_workspace(workspace_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_workspace(workspace_id, payload, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/workspaces/{workspace_id}/select", name="ncp008_workspaces_select")
    def select_workspace(workspace_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.select_workspace(workspace_id, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/workspaces/{workspace_id}/archive", name="ncp008_workspaces_archive")
    def archive_workspace(workspace_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.archive_workspace(workspace_id, _ctx(claims, request or Request({"type": "http"})))

    @router.get("/workspaces/{workspace_id}/summary", name="ncp008_workspaces_summary")
    def workspace_summary(workspace_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.workspace_summary(workspace_id, _ctx(claims, request or Request({"type": "http"})))

    # Environments
    @router.get("/environments", name="ncp008_environments_list")
    def list_environments(limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        items = service.list_environments(ctx)
        return {"environments": _paginate_list(items, limit=limit, offset=offset), "count": len(items)}

    @router.post("/environments", name="ncp008_environments_create")
    def create_environment(payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None, x_idempotency_key: str | None = Header(default=None)) -> dict[str, Any]:
        return service.create_environment(payload, _ctx(claims, request or Request({"type": "http"})), idempotency_key=x_idempotency_key or str(payload.get("idempotency_key") or ""))

    @router.get("/environments/{environment_id}", name="ncp008_environments_get")
    def get_environment(environment_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"environment": service.get_environment(environment_id, _ctx(claims, request or Request({"type": "http"})))}

    @router.patch("/environments/{environment_id}", name="ncp008_environments_update")
    def update_environment(environment_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_environment(environment_id, payload, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/environments/{environment_id}/transition", name="ncp008_environments_transition")
    def transition_environment(environment_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.transition_environment(environment_id, str(payload.get("status") or payload.get("target_status") or ""), _ctx(claims, request or Request({"type": "http"})))

    @router.post("/environments/{environment_id}/freeze", name="ncp008_environments_freeze")
    def freeze_environment(environment_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.freeze_environment(environment_id, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/environments/{environment_id}/unfreeze", name="ncp008_environments_unfreeze")
    def unfreeze_environment(environment_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.unfreeze_environment(environment_id, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/environments/{environment_id}/archive", name="ncp008_environments_archive")
    def archive_environment(environment_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.archive_environment(environment_id, _ctx(claims, request or Request({"type": "http"})))

    @router.get("/environments/{environment_id}/summary", name="ncp008_environments_summary")
    def environment_summary(environment_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.environment_summary(environment_id, _ctx(claims, request or Request({"type": "http"})))

    @router.get("/environments/{environment_id}/health", name="ncp008_environments_health")
    def environment_health(environment_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.environment_health(environment_id, _ctx(claims, request or Request({"type": "http"})))

    @router.get("/environments/{environment_id}/risk", name="ncp008_environments_risk")
    def environment_risk(environment_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.environment_risk(environment_id, _ctx(claims, request or Request({"type": "http"})))

    # Services
    @router.get("/services", name="ncp008_services_list")
    def list_services(limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        items = service.list_services(ctx)
        return {"services": _paginate_list(items, limit=limit, offset=offset), "count": len(items)}

    @router.post("/services", name="ncp008_services_create")
    def create_service(payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None, x_idempotency_key: str | None = Header(default=None)) -> dict[str, Any]:
        return service.create_service(payload, _ctx(claims, request or Request({"type": "http"})), idempotency_key=x_idempotency_key or str(payload.get("idempotency_key") or ""))

    @router.get("/services/{service_id}", name="ncp008_services_get")
    def get_service(service_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"service": service.get_service(service_id, _ctx(claims, request or Request({"type": "http"})))}

    @router.patch("/services/{service_id}", name="ncp008_services_update")
    def update_service(service_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_service(service_id, payload, _ctx(claims, request or Request({"type": "http"})))

    @router.get("/services/{service_id}/health", name="ncp008_services_health")
    def service_health(service_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.service_health(service_id, _ctx(claims, request or Request({"type": "http"})))

    @router.get("/services/{service_id}/dependencies", name="ncp008_services_dependencies")
    def service_dependencies(service_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.service_dependencies(service_id, _ctx(claims, request or Request({"type": "http"})))

    @router.get("/services/{service_id}/deployments", name="ncp008_services_deployments")
    def service_deployments(service_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"deployments": service.service_deployments(service_id, _ctx(claims, request or Request({"type": "http"})))}

    @router.get("/services/{service_id}/metrics", name="ncp008_services_metrics")
    def service_metrics(service_id: str, query: str = Query(default="up"), window_seconds: int = Query(default=3600, ge=60, le=86400), limit: int = Query(default=100, ge=1, le=1000), claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.service_metrics(service_id, _ctx(claims, request or Request({"type": "http"})), query=query, window_seconds=window_seconds, limit=limit)

    @router.get("/services/{service_id}/logs", name="ncp008_services_logs")
    def service_logs(service_id: str, query: str = Query(default=""), window_seconds: int = Query(default=3600, ge=60, le=86400), limit: int = Query(default=100, ge=1, le=1000), claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.service_logs(service_id, _ctx(claims, request or Request({"type": "http"})), query=query, window_seconds=window_seconds, limit=limit)

    @router.get("/services/{service_id}/traces", name="ncp008_services_traces")
    def service_traces(service_id: str, query: str = Query(default=""), window_seconds: int = Query(default=3600, ge=60, le=86400), limit: int = Query(default=100, ge=1, le=1000), claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.service_traces(service_id, _ctx(claims, request or Request({"type": "http"})), query=query, window_seconds=window_seconds, limit=limit)

    # Deployments
    @router.get("/deployments", name="ncp008_deployments_list")
    def list_deployments(limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        items = service.list_deployments(ctx)
        return {"deployments": _paginate_list(items, limit=limit, offset=offset), "count": len(items)}

    @router.get("/deployments/{deployment_id}", name="ncp008_deployments_get")
    def get_deployment(deployment_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"deployment": service.get_deployment(deployment_id, _ctx(claims, request or Request({"type": "http"})))}

    @router.get("/deployments/{deployment_id}/evidence", name="ncp008_deployments_evidence")
    def deployment_evidence(deployment_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"evidence": service.deployment_evidence(deployment_id, _ctx(claims, request or Request({"type": "http"})))}

    @router.post("/deployments/{deployment_id}/rollback-requests", name="ncp008_deployments_rollback_requests")
    def request_rollback(deployment_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None, x_idempotency_key: str | None = Header(default=None)) -> dict[str, Any]:
        return service.request_deployment_rollback(deployment_id, payload, _ctx(claims, request or Request({"type": "http"})), idempotency_key=x_idempotency_key or str(payload.get("idempotency_key") or ""))

    @router.get("/deployments/{deployment_id}/verification", name="ncp008_deployments_verification")
    def deployment_verification(deployment_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.deployment_verification(deployment_id, _ctx(claims, request or Request({"type": "http"})))

    # Health checks
    _collection_crud(router, service=service, base_path="/health/checks", kind="health_check_definition", list_key="checks", singular_key="check", read_permission="operations.read", write_permission="operations.action.request")

    @router.get("/health", name="ncp008_health_overview")
    def health_overview(claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        return {"status": "ok", "environment_health": [service.environment_health(environment["id"], ctx) for environment in service.list_environments(ctx)], "service_health": [service.service_health(runtime_service["id"], ctx) for runtime_service in service.list_services(ctx)]}

    @router.get("/health/services/{service_id}", name="ncp008_health_service")
    def health_service(service_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.service_health(service_id, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/health/checks/{check_id}/execute", name="ncp008_health_check_execute")
    def execute_health_check(check_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        check = service.get_collection_item("health_check_definition", check_id, ctx)
        execution = service.create_collection_item("health_check_execution", {"health_check_id": check_id, "service_id": check.get("service_id"), "environment_id": check.get("environment_id"), "status": "SUCCEEDED", "result": service.service_health(str(check.get("service_id") or ""), ctx)}, ctx, status="SUCCEEDED")
        return {"check": check, "execution": execution}

    @router.get("/health/checks/{check_id}/executions", name="ncp008_health_check_executions")
    def list_health_check_executions(check_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        executions = [record for record in service.list_collection("health_check_execution", ctx) if record.get("health_check_id") == check_id]
        return {"executions": executions}

    @router.post("/health/snapshots", name="ncp008_health_snapshots_create")
    def create_health_snapshot(payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None, x_idempotency_key: str | None = Header(default=None)) -> dict[str, Any]:
        return service.create_collection_item("health_snapshot", payload, _ctx(claims, request or Request({"type": "http"})), idempotency_key=x_idempotency_key or str(payload.get("idempotency_key") or ""), status=payload.get("status") or "CREATED")

    @router.get("/health/snapshots/{snapshot_id}", name="ncp008_health_snapshots_get")
    def get_health_snapshot(snapshot_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"snapshot": service.get_collection_item("health_snapshot", snapshot_id, _ctx(claims, request or Request({"type": "http"})))}

    # Telemetry
    @router.post("/telemetry/metrics/query", name="ncp008_telemetry_metrics_query")
    def query_metrics(payload: dict[str, Any], claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        return service.observability.query_metrics(organization_id=ctx.organization_id, environment_id=payload.get("environment_id"), service_id=payload.get("service_id"), query=str(payload.get("query") or "up"), time_range_seconds=min(int(payload.get("time_range_seconds") or 3600), 86400), limit=min(int(payload.get("limit") or 100), 1000))

    @router.post("/telemetry/logs/query", name="ncp008_telemetry_logs_query")
    def query_logs(payload: dict[str, Any], claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        return service.observability.query_logs(organization_id=ctx.organization_id, environment_id=payload.get("environment_id"), service_id=payload.get("service_id"), query=str(payload.get("query") or ""), time_range_seconds=min(int(payload.get("time_range_seconds") or 3600), 86400), limit=min(int(payload.get("limit") or 100), 1000))

    @router.post("/telemetry/traces/query", name="ncp008_telemetry_traces_query")
    def query_traces(payload: dict[str, Any], claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        return service.observability.query_traces(organization_id=ctx.organization_id, environment_id=payload.get("environment_id"), service_id=payload.get("service_id"), query=str(payload.get("query") or ""), time_range_seconds=min(int(payload.get("time_range_seconds") or 3600), 86400), limit=min(int(payload.get("limit") or 100), 1000))

    @router.get("/telemetry/services/{service_id}/overview", name="ncp008_telemetry_service_overview")
    def service_overview(service_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        return {"service": service.service_health(service_id, ctx), "metrics": service.service_metrics(service_id, ctx), "logs": service.service_logs(service_id, ctx), "traces": service.service_traces(service_id, ctx)}

    @router.get("/telemetry/services/{service_id}/metrics", name="ncp008_telemetry_service_metrics")
    def telemetry_service_metrics(service_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.service_metrics(service_id, _ctx(claims, request or Request({"type": "http"})))

    @router.get("/telemetry/services/{service_id}/logs", name="ncp008_telemetry_service_logs")
    def telemetry_service_logs(service_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.service_logs(service_id, _ctx(claims, request or Request({"type": "http"})))

    @router.get("/telemetry/services/{service_id}/traces", name="ncp008_telemetry_service_traces")
    def telemetry_service_traces(service_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.service_traces(service_id, _ctx(claims, request or Request({"type": "http"})))

    @router.get("/telemetry/correlations/{correlation_id}", name="ncp008_telemetry_correlation")
    def telemetry_correlation(correlation_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"correlation_id": correlation_id, "activity": [event for event in service.activity(_ctx(claims, request or Request({"type": "http"}))) if str(event.get("correlation_id") or "") == correlation_id]}

    # Alerts
    @router.post("/alerts", name="ncp008_alerts_create")
    def create_alert(payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None, x_idempotency_key: str | None = Header(default=None)) -> dict[str, Any]:
        return service.create_alert(payload, _ctx(claims, request or Request({"type": "http"})), idempotency_key=x_idempotency_key or str(payload.get("idempotency_key") or ""))

    @router.get("/alerts", name="ncp008_alerts_list")
    def list_alerts(limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        items = service.list_alerts(ctx)
        return {"alerts": _paginate_list(items, limit=limit, offset=offset), "count": len(items)}

    @router.get("/alerts/{alert_id}", name="ncp008_alerts_get")
    def get_alert(alert_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"alert": service.get_alert(alert_id, _ctx(claims, request or Request({"type": "http"})))}

    @router.post("/alerts/{alert_id}/acknowledge", name="ncp008_alerts_acknowledge")
    def acknowledge_alert(alert_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.acknowledge_alert(alert_id, payload, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/alerts/{alert_id}/resolve", name="ncp008_alerts_resolve")
    def resolve_alert(alert_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.resolve_alert(alert_id, payload, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/alerts/{alert_id}/incident", name="ncp008_alerts_incident")
    def alert_to_incident(alert_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None, x_idempotency_key: str | None = Header(default=None)) -> dict[str, Any]:
        return service.alert_to_incident(alert_id, payload, _ctx(claims, request or Request({"type": "http"})), idempotency_key=x_idempotency_key or str(payload.get("idempotency_key") or ""))

    # Incidents
    @router.post("/incidents", name="ncp008_incidents_create")
    def create_incident(payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None, x_idempotency_key: str | None = Header(default=None)) -> dict[str, Any]:
        return service.create_incident(payload, _ctx(claims, request or Request({"type": "http"})), idempotency_key=x_idempotency_key or str(payload.get("idempotency_key") or ""))

    @router.get("/incidents", name="ncp008_incidents_list")
    def list_incidents(limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        items = service.list_incidents(ctx)
        return {"incidents": _paginate_list(items, limit=limit, offset=offset), "count": len(items)}

    @router.get("/incidents/{incident_id}", name="ncp008_incidents_get")
    def get_incident(incident_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"incident": service.get_incident(incident_id, _ctx(claims, request or Request({"type": "http"})))}

    @router.patch("/incidents/{incident_id}", name="ncp008_incidents_update")
    def update_incident(incident_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_incident(incident_id, payload, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/incidents/{incident_id}/transition", name="ncp008_incidents_transition")
    def transition_incident(incident_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.transition_incident(incident_id, str(payload.get("status") or payload.get("target_status") or ""), _ctx(claims, request or Request({"type": "http"})))

    @router.post("/incidents/{incident_id}/assignments", name="ncp008_incidents_assignments")
    def assign_incident(incident_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.assign_incident(incident_id, payload, _ctx(claims, request or Request({"type": "http"})))

    @router.get("/incidents/{incident_id}/timeline", name="ncp008_incidents_timeline_list")
    def get_incident_timeline(incident_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"timeline": service.incident_timeline(incident_id, _ctx(claims, request or Request({"type": "http"})))}

    @router.post("/incidents/{incident_id}/timeline", name="ncp008_incidents_timeline_create")
    def add_incident_timeline(incident_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None, x_idempotency_key: str | None = Header(default=None)) -> dict[str, Any]:
        return service.add_incident_timeline_event(incident_id, payload, _ctx(claims, request or Request({"type": "http"})), idempotency_key=x_idempotency_key or str(payload.get("idempotency_key") or ""))

    @router.get("/incidents/{incident_id}/evidence", name="ncp008_incidents_evidence")
    def incident_evidence(incident_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"evidence": service.incident_evidence(incident_id, _ctx(claims, request or Request({"type": "http"})))}

    @router.post("/incidents/{incident_id}/post-incident-reviews", name="ncp008_incidents_reviews")
    def create_incident_review(incident_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None, x_idempotency_key: str | None = Header(default=None)) -> dict[str, Any]:
        return service.create_post_incident_review(incident_id, payload, _ctx(claims, request or Request({"type": "http"})), idempotency_key=x_idempotency_key or str(payload.get("idempotency_key") or ""))

    # Actions
    @router.post("/actions", name="ncp008_actions_create")
    def create_action(payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None, x_idempotency_key: str | None = Header(default=None)) -> dict[str, Any]:
        return service.create_action(payload, _ctx(claims, request or Request({"type": "http"})), idempotency_key=x_idempotency_key or str(payload.get("idempotency_key") or ""))

    @router.get("/actions", name="ncp008_actions_list")
    def list_actions(limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        items = service.list_actions(ctx)
        return {"actions": _paginate_list(items, limit=limit, offset=offset), "count": len(items)}

    @router.get("/actions/{action_id}", name="ncp008_actions_get")
    def get_action(action_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"action": service.get_action(action_id, _ctx(claims, request or Request({"type": "http"})))}

    @router.post("/actions/{action_id}/evaluate", name="ncp008_actions_evaluate")
    def evaluate_action(action_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.evaluate_action({"action_id": action_id, **payload}, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/actions/{action_id}/approval-requests", name="ncp008_actions_approval_requests")
    def action_approval_request(action_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.request_action_approval(action_id, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/actions/{action_id}/approve", name="ncp008_actions_approve")
    def action_approve(action_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.approve_action(action_id, payload, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/actions/{action_id}/reject", name="ncp008_actions_reject")
    def action_reject(action_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.reject_action(action_id, payload, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/actions/{action_id}/execute", name="ncp008_actions_execute")
    def action_execute(action_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.execute_action(action_id, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/actions/{action_id}/verify", name="ncp008_actions_verify")
    def action_verify(action_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return service.verify_action(action_id, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/actions/{action_id}/cancel", name="ncp008_actions_cancel")
    def action_cancel(action_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.cancel_action(action_id, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/actions/{action_id}/rollback", name="ncp008_actions_rollback")
    def action_rollback(action_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.rollback_action(action_id, _ctx(claims, request or Request({"type": "http"})))

    @router.get("/actions/{action_id}/evidence", name="ncp008_actions_evidence")
    def action_evidence(action_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"evidence": service.action_evidence(action_id, _ctx(claims, request or Request({"type": "http"})))}

    # SLOs
    @router.post("/slos", name="ncp008_slos_create")
    def create_slo(payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None, x_idempotency_key: str | None = Header(default=None)) -> dict[str, Any]:
        return service.create_slo(payload, _ctx(claims, request or Request({"type": "http"})), idempotency_key=x_idempotency_key or str(payload.get("idempotency_key") or ""))

    @router.get("/slos", name="ncp008_slos_list")
    def list_slos(limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        items = service.list_slos(ctx)
        return {"slos": _paginate_list(items, limit=limit, offset=offset), "count": len(items)}

    @router.get("/slos/{slo_id}", name="ncp008_slos_get")
    def get_slo(slo_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"slo": service.get_slo(slo_id, _ctx(claims, request or Request({"type": "http"})))}

    @router.patch("/slos/{slo_id}", name="ncp008_slos_update")
    def update_slo(slo_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_slo(slo_id, payload, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/slos/{slo_id}/evaluate", name="ncp008_slos_evaluate")
    def evaluate_slo(slo_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.evaluate_slo(slo_id, _ctx(claims, request or Request({"type": "http"})))

    @router.get("/slos/{slo_id}/history", name="ncp008_slos_history")
    def slo_history(slo_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"measurements": service.slo_history(slo_id, _ctx(claims, request or Request({"type": "http"})))}

    # Recovery plans
    @router.post("/recovery-plans/{plan_id}/validate", name="ncp008_recovery_validate")
    def validate_recovery_plan(plan_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.validate_recovery_plan(plan_id, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/recovery-plans/{plan_id}/execute", name="ncp008_recovery_execute")
    def execute_recovery_plan(plan_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.execute_recovery_plan(plan_id, _ctx(claims, request or Request({"type": "http"})))

    @router.get("/recovery-plans", name="ncp008_recovery_list")
    def list_recovery_plans(limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        items = service.list_recovery_plans(ctx)
        return {"recovery_plans": _paginate_list(items, limit=limit, offset=offset), "count": len(items)}

    @router.post("/recovery-plans", name="ncp008_recovery_create")
    def create_recovery_plan(payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None, x_idempotency_key: str | None = Header(default=None)) -> dict[str, Any]:
        return service.create_recovery_plan(payload, _ctx(claims, request or Request({"type": "http"})), idempotency_key=x_idempotency_key or str(payload.get("idempotency_key") or ""))

    @router.get("/recovery-plans/{plan_id}", name="ncp008_recovery_get")
    def get_recovery_plan(plan_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"recovery_plan": service.get_recovery_plan(plan_id, _ctx(claims, request or Request({"type": "http"})))}

    @router.patch("/recovery-plans/{plan_id}", name="ncp008_recovery_update")
    def update_recovery_plan(plan_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_recovery_plan(plan_id, payload, _ctx(claims, request or Request({"type": "http"})))

    # Post incident reviews
    @router.get("/post-incident-reviews", name="ncp008_post_incident_reviews_list")
    def list_post_incident_reviews(limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        items = service.list_post_incident_reviews(ctx)
        return {"post_incident_reviews": _paginate_list(items, limit=limit, offset=offset), "count": len(items)}

    @router.get("/post-incident-reviews/{review_id}", name="ncp008_post_incident_reviews_get")
    def get_post_incident_review(review_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"post_incident_review": service.get_post_incident_review(review_id, _ctx(claims, request or Request({"type": "http"})))}

    @router.patch("/post-incident-reviews/{review_id}", name="ncp008_post_incident_reviews_update")
    def update_post_incident_review(review_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_post_incident_review(review_id, payload, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/post-incident-reviews/{review_id}/publish", name="ncp008_post_incident_reviews_publish")
    def publish_post_incident_review(review_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.publish_post_incident_review(review_id, _ctx(claims, request or Request({"type": "http"})))

    # On-call and escalation
    _collection_crud(router, service=service, base_path="/on-call/schedules", kind="on_call_schedule", list_key="schedules", singular_key="schedule", read_permission="operations.read", write_permission="operations.action.request")
    _collection_crud(router, service=service, base_path="/escalation-policies", kind="escalation_policy", list_key="policies", singular_key="policy", read_permission="operations.read", write_permission="operations.action.request")

    @router.get("/on-call/schedules/{schedule_id}/current", name="ncp008_on_call_current")
    def current_schedule(schedule_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        return {"schedule": service.get_collection_item("on_call_schedule", schedule_id, ctx), "current": []}

    @router.post("/on-call/schedules/{schedule_id}/overrides", name="ncp008_on_call_overrides")
    def schedule_override(schedule_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        return service.create_collection_item("on_call_override", {"schedule_id": schedule_id, **payload}, ctx, status=payload.get("status") or "ACTIVE")

    @router.post("/escalation-policies/{policy_id}/execute", name="ncp008_escalation_execute")
    def execute_escalation(policy_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        policy = service.get_collection_item("escalation_policy", policy_id, ctx)
        return {"policy": policy, "executions": [payload]}

    # Change management / rollback / backup / DR / capacity / maintenance / runbooks / commands / postmortems / baselines
    for base_path, kind, list_key, singular_key, read_perm, write_perm in [
        ("/changes", "operational_change", "changes", "change", "operations.read", "operations.action.request"),
        ("/change-windows", "change_window", "change_windows", "change_window", "operations.read", "operations.action.request"),
        ("/change-freezes", "change_freeze", "change_freezes", "change_freeze", "operations.read", "operations.action.request"),
        ("/rollbacks", "rollback", "rollbacks", "rollback", "operations.deployment.read", "operations.deployment.rollback"),
        ("/backups/policies", "backup_policy", "backup_policies", "backup_policy", "operations.read", "operations.action.request"),
        ("/backups", "backup_record", "backups", "backup", "operations.read", "operations.action.request"),
        ("/restores", "restore_plan", "restores", "restore", "operations.read", "operations.action.request"),
        ("/failover-plans", "failover_plan", "failover_plans", "failover_plan", "operations.read", "operations.action.request"),
        ("/disaster-recovery/plans", "disaster_recovery_plan", "disaster_recovery_plans", "disaster_recovery_plan", "operations.read", "operations.action.request"),
        ("/disaster-recovery/exercises", "disaster_recovery_exercise", "disaster_recovery_exercises", "disaster_recovery_exercise", "operations.read", "operations.action.request"),
        ("/capacity", "capacity_measurement", "capacity", "capacity_measurement", "operations.read", "operations.action.request"),
        ("/capacity/forecasts", "capacity_forecast", "capacity_forecasts", "capacity_forecast", "operations.read", "operations.action.request"),
        ("/scaling-policies", "scaling_policy", "scaling_policies", "scaling_policy", "operations.read", "operations.action.request"),
        ("/scaling-actions", "scaling_action", "scaling_actions", "scaling_action", "operations.read", "operations.action.request"),
        ("/maintenance/windows", "maintenance_window", "maintenance_windows", "maintenance_window", "operations.read", "operations.action.request"),
        ("/maintenance/tasks", "maintenance_task", "maintenance_tasks", "maintenance_task", "operations.read", "operations.action.request"),
        ("/runbooks", "runbook", "runbooks", "runbook", "operations.recovery.read", "operations.recovery.manage"),
        ("/runbook-executions", "runbook_execution", "runbook_executions", "runbook_execution", "operations.recovery.read", "operations.recovery.manage"),
        ("/commands", "operational_command", "commands", "command", "operations.read", "operations.action.request"),
        ("/postmortems", "postmortem", "postmortems", "postmortem", "operations.postmortem.read", "operations.postmortem.write"),
        ("/corrective-actions", "corrective_action", "corrective_actions", "corrective_action", "operations.postmortem.read", "operations.postmortem.write"),
        ("/baselines", "operational_baseline", "baselines", "baseline", "operations.read", "operations.action.request"),
    ]:
        _collection_crud(router, service=service, base_path=base_path, kind=kind, list_key=list_key, singular_key=singular_key, read_permission=read_perm, write_permission=write_perm)

    @router.post("/rollbacks/{rollback_id}/validate", name="ncp008_rollbacks_validate")
    def validate_rollback(rollback_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return {"rollback": service.get_collection_item("rollback", rollback_id, _ctx(claims, request or Request({"type": "http"}))), "validation": "valid"}

    @router.post("/rollbacks/{rollback_id}/approve", name="ncp008_rollbacks_approve")
    def approve_rollback(rollback_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("rollback", rollback_id, {"approval_status": "APPROVED"}, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/rollbacks/{rollback_id}/execute", name="ncp008_rollbacks_execute")
    def execute_rollback(rollback_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        rollback = service.get_collection_item("rollback", rollback_id, ctx)
        return service.update_collection_item("rollback", rollback_id, {"status": "SUCCEEDED", "verification_status": "VERIFIED", "result": {"rollback_id": rollback_id}}, ctx, status="SUCCEEDED")

    @router.post("/rollbacks/{rollback_id}/verify", name="ncp008_rollbacks_verify")
    def verify_rollback(rollback_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"rollback": service.get_collection_item("rollback", rollback_id, _ctx(claims, request or Request({"type": "http"}))), "verification": "verified"}

    @router.post("/rollbacks/{rollback_id}/cancel", name="ncp008_rollbacks_cancel")
    def cancel_rollback(rollback_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("rollback", rollback_id, {"status": "CANCELLED"}, _ctx(claims, request or Request({"type": "http"})), status="CANCELLED")

    @router.post("/backups/{backup_id}/execute", name="ncp008_backups_execute")
    def execute_backup(backup_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("backup_record", backup_id, {"status": "SUCCEEDED"}, _ctx(claims, request or Request({"type": "http"})), status="SUCCEEDED")

    @router.post("/backups/{backup_id}/verify", name="ncp008_backups_verify")
    def verify_backup(backup_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"backup": service.get_collection_item("backup_record", backup_id, _ctx(claims, request or Request({"type": "http"}))), "verification": "verified"}

    @router.post("/restores/{restore_id}/validate", name="ncp008_restores_validate")
    def validate_restore(restore_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return {"restore": service.get_collection_item("restore_plan", restore_id, _ctx(claims, request or Request({"type": "http"}))), "validation": "valid"}

    @router.post("/restores/{restore_id}/approve", name="ncp008_restores_approve")
    def approve_restore(restore_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("restore_plan", restore_id, {"approval_status": "APPROVED"}, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/restores/{restore_id}/execute", name="ncp008_restores_execute")
    def execute_restore(restore_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("restore_plan", restore_id, {"status": "SUCCEEDED"}, _ctx(claims, request or Request({"type": "http"})), status="SUCCEEDED")

    @router.post("/restores/{restore_id}/verify", name="ncp008_restores_verify")
    def verify_restore(restore_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"restore": service.get_collection_item("restore_plan", restore_id, _ctx(claims, request or Request({"type": "http"}))), "verification": "verified"}

    @router.post("/failover-plans/{plan_id}/validate", name="ncp008_failover_validate")
    def validate_failover(plan_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return {"failover_plan": service.get_collection_item("failover_plan", plan_id, _ctx(claims, request or Request({"type": "http"}))), "validation": "valid"}

    @router.post("/failover-plans/{plan_id}/execute", name="ncp008_failover_execute")
    def execute_failover(plan_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("failover_plan", plan_id, {"status": "SUCCEEDED"}, _ctx(claims, request or Request({"type": "http"})), status="SUCCEEDED")

    @router.post("/failover-plans/{plan_id}/verify", name="ncp008_failover_verify")
    def verify_failover(plan_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"failover_plan": service.get_collection_item("failover_plan", plan_id, _ctx(claims, request or Request({"type": "http"}))), "verification": "verified"}

    @router.post("/disaster-recovery/exercises/{exercise_id}/execute", name="ncp008_dr_execute")
    def execute_dr(exercise_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("disaster_recovery_exercise", exercise_id, {"status": "SUCCEEDED"}, _ctx(claims, request or Request({"type": "http"})), status="SUCCEEDED")

    @router.post("/disaster-recovery/exercises/{exercise_id}/verify", name="ncp008_dr_verify")
    def verify_dr(exercise_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"exercise": service.get_collection_item("disaster_recovery_exercise", exercise_id, _ctx(claims, request or Request({"type": "http"}))), "verification": "verified"}

    @router.post("/disaster-recovery/exercises/{exercise_id}/complete", name="ncp008_dr_complete")
    def complete_dr(exercise_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("disaster_recovery_exercise", exercise_id, {"status": "COMPLETED"}, _ctx(claims, request or Request({"type": "http"})), status="COMPLETED")

    @router.post("/scaling-policies/{policy_id}/evaluate", name="ncp008_scaling_policy_evaluate")
    def evaluate_scaling_policy(policy_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return {"scaling_policy": service.get_collection_item("scaling_policy", policy_id, _ctx(claims, request or Request({"type": "http"}))), "decision": "allow"}

    @router.post("/scaling-actions/{action_id}/execute", name="ncp008_scaling_execute")
    def execute_scaling_action(action_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("scaling_action", action_id, {"status": "SUCCEEDED"}, _ctx(claims, request or Request({"type": "http"})), status="SUCCEEDED")

    @router.post("/scaling-actions/{action_id}/verify", name="ncp008_scaling_verify")
    def verify_scaling_action(action_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"scaling_action": service.get_collection_item("scaling_action", action_id, _ctx(claims, request or Request({"type": "http"}))), "verification": "verified"}

    @router.post("/maintenance/tasks/{task_id}/approve", name="ncp008_maintenance_approve")
    def approve_maintenance(task_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("maintenance_task", task_id, {"approval_status": "APPROVED"}, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/maintenance/tasks/{task_id}/execute", name="ncp008_maintenance_execute")
    def execute_maintenance(task_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("maintenance_task", task_id, {"status": "SUCCEEDED"}, _ctx(claims, request or Request({"type": "http"})), status="SUCCEEDED")

    @router.post("/maintenance/tasks/{task_id}/verify", name="ncp008_maintenance_verify")
    def verify_maintenance(task_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"maintenance_task": service.get_collection_item("maintenance_task", task_id, _ctx(claims, request or Request({"type": "http"}))), "verification": "verified"}

    @router.post("/maintenance/tasks/{task_id}/rollback", name="ncp008_maintenance_rollback")
    def rollback_maintenance(task_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("maintenance_task", task_id, {"status": "ROLLED_BACK"}, _ctx(claims, request or Request({"type": "http"})), status="ROLLED_BACK")

    @router.post("/runbooks/{runbook_id}/execute", name="ncp008_runbooks_execute")
    def execute_runbook(runbook_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None, x_idempotency_key: str | None = Header(default=None)) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        execution = service.create_collection_item("runbook_execution", {"runbook_id": runbook_id, "status": "RUNNING", "inputs": payload, "started_at": payload.get("started_at") or ""}, ctx, idempotency_key=x_idempotency_key or str(payload.get("idempotency_key") or ""), status="RUNNING")
        return {"runbook_execution": execution}

    @router.get("/runbook-executions/{execution_id}", name="ncp008_runbook_execution_get")
    def get_runbook_execution(execution_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"runbook_execution": service.get_collection_item("runbook_execution", execution_id, _ctx(claims, request or Request({"type": "http"})))}

    @router.post("/runbook-executions/{execution_id}/approve", name="ncp008_runbook_execution_approve")
    def approve_runbook_execution(execution_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("runbook_execution", execution_id, {"status": "APPROVED"}, _ctx(claims, request or Request({"type": "http"})), status="APPROVED")

    @router.post("/runbook-executions/{execution_id}/continue", name="ncp008_runbook_execution_continue")
    def continue_runbook_execution(execution_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("runbook_execution", execution_id, {"status": "RUNNING"}, _ctx(claims, request or Request({"type": "http"})), status="RUNNING")

    @router.post("/runbook-executions/{execution_id}/pause", name="ncp008_runbook_execution_pause")
    def pause_runbook_execution(execution_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("runbook_execution", execution_id, {"status": "PAUSED"}, _ctx(claims, request or Request({"type": "http"})), status="PAUSED")

    @router.post("/runbook-executions/{execution_id}/cancel", name="ncp008_runbook_execution_cancel")
    def cancel_runbook_execution(execution_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("runbook_execution", execution_id, {"status": "CANCELLED"}, _ctx(claims, request or Request({"type": "http"})), status="CANCELLED")

    @router.post("/runbook-executions/{execution_id}/rollback", name="ncp008_runbook_execution_rollback")
    def rollback_runbook_execution(execution_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("runbook_execution", execution_id, {"status": "ROLLED_BACK"}, _ctx(claims, request or Request({"type": "http"})), status="ROLLED_BACK")

    @router.post("/runbook-executions/{execution_id}/verify", name="ncp008_runbook_execution_verify")
    def verify_runbook_execution(execution_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        return {"runbook_execution": service.get_collection_item("runbook_execution", execution_id, _ctx(claims, request or Request({"type": "http"}))), "verification": "verified"}

    # Additional generic operations
    _collection_crud(router, service=service, base_path="/alerts/rules", kind="alert_rule", list_key="rules", singular_key="rule", read_permission="operations.alert.read", write_permission="operations.action.request")
    _collection_crud(router, service=service, base_path="/incident-timeline", kind="incident_timeline_event", list_key="events", singular_key="event", read_permission="operations.incident.read", write_permission="operations.timeline.write")
    _collection_crud(router, service=service, base_path="/slis", kind="sli", list_key="slis", singular_key="sli", read_permission="operations.slo.read", write_permission="operations.action.request")
    _collection_crud(router, service=service, base_path="/error-budgets", kind="error_budget_policy", list_key="error_budgets", singular_key="error_budget", read_permission="operations.slo.read", write_permission="operations.action.request")
    _collection_crud(router, service=service, base_path="/operational-dashboards", kind="operational_dashboard", list_key="dashboards", singular_key="dashboard", read_permission="operations.read", write_permission="operations.action.request")

    @router.post("/incidents/{incident_id}/resolve", name="ncp008_incidents_resolve")
    def resolve_incident(incident_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.transition_incident(incident_id, "RESOLVED", _ctx(claims, request or Request({"type": "http"})))

    @router.post("/incidents/{incident_id}/close", name="ncp008_incidents_close")
    def close_incident(incident_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.transition_incident(incident_id, "CLOSED", _ctx(claims, request or Request({"type": "http"})))

    @router.post("/incidents/{incident_id}/communications", name="ncp008_incident_communications_create")
    def create_communication(incident_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.create_collection_item("incident_communication", {"incident_id": incident_id, **payload}, _ctx(claims, request or Request({"type": "http"})), status=payload.get("status") or "DRAFT")

    @router.get("/incidents/{incident_id}/communications", name="ncp008_incident_communications_list")
    def list_communications(incident_id: str, claims: JWTClaims = Depends(read_claims), request: Request = None) -> dict[str, Any]:
        ctx = _ctx(claims, request or Request({"type": "http"}))
        return {"communications": [record for record in service.list_collection("incident_communication", ctx) if record.get("incident_id") == incident_id]}

    @router.post("/postmortems/{postmortem_id}/review", name="ncp008_postmortems_review")
    def review_postmortem(postmortem_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("postmortem", postmortem_id, {"review_status": "REVIEWED"}, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/postmortems/{postmortem_id}/approve", name="ncp008_postmortems_approve")
    def approve_postmortem(postmortem_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("postmortem", postmortem_id, {"approval_status": "APPROVED"}, _ctx(claims, request or Request({"type": "http"})))

    @router.post("/postmortems/{postmortem_id}/publish", name="ncp008_postmortems_publish")
    def publish_postmortem(postmortem_id: str, claims: JWTClaims = Depends(write_claims), request: Request = None) -> dict[str, Any]:
        return service.update_collection_item("postmortem", postmortem_id, {"publication_status": "PUBLISHED"}, _ctx(claims, request or Request({"type": "http"})))

    return router
