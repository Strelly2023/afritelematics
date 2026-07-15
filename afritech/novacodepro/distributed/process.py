from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

from afritech.api.auth.jwt_device_auth import build_auth_router
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.api.novacodepro_workflow_fabric_api import build_novacodepro_workflow_fabric_router
from afritech.api.solution_engineering_api import build_solution_engineering_router
from afritech.novacodepro.platform import NovaCodeProPlatform, NovaCodeProRepository, get_novacodepro_platform
from afritech.novacodepro.distributed.broker import build_durable_event_broker
from afritech.novacodepro.distributed.tracing import DistributedTracingMiddleware
from afritech.novacodepro.distributed.workers import AgentExecutionWorker, OutboxWorker
from afritech.novacodepro.service_registry import get_service_definition
from afritech.novacodepro.workflow_fabric import WorkflowFabricService


def _db_path_from_env(env_var: str, default_name: str) -> Path:
    return Path(os.environ.get(env_var, f"var/novacodepro/{default_name}.sqlite3"))


SERVICE_ROUTE_ALLOWLIST: dict[str, tuple[str, ...]] = {
    "gateway": ("/health", "/ready", "/metrics", "/v1/auth/", "/v1/devices/", "/v1/outbox"),
    "identity-context": ("/health", "/ready", "/metrics"),
    "tenant": ("/health", "/ready", "/metrics"),
    "federation": ("/health", "/ready", "/metrics", "/v1/novacodepro/federation/", "/v1/novacodepro/regions/"),
    "solution": ("/health", "/ready", "/metrics", "/v1/novacodepro/solutions", "/v1/novacodepro/workflows", "/v1/novacodepro/projects", "/v1/novacodepro/artifacts"),
    "workflow": ("/health", "/ready", "/metrics", "/v1/novacodepro/workflows", "/v1/workflows", "/v1/workflow-fabric", "/v1/outbox"),
    "approval": ("/health", "/ready", "/metrics", "/v1/novacodepro/approvals"),
    "agent": ("/health", "/ready", "/metrics", "/v1/novacodepro/agents", "/v1/outbox", "/v1/workers/agents/drain"),
    "evidence": ("/health", "/ready", "/metrics", "/v1/novacodepro/evidence/"),
    "risk": ("/health", "/ready", "/metrics", "/v1/novacodepro/risks"),
    "policy": ("/health", "/ready", "/metrics", "/v1/novacodepro/policies"),
    "knowledge": ("/health", "/ready", "/metrics", "/v1/novacodepro/knowledge", "/v1/novacodepro/graph"),
    "graph": ("/health", "/ready", "/metrics", "/v1/novacodepro/knowledge", "/v1/novacodepro/graph"),
    "digital-twin": ("/health", "/ready", "/metrics", "/v1/novacodepro/digital-twins", "/v1/novacodepro/twins", "/v1/novacodepro/eros"),
    "release": ("/health", "/ready", "/metrics", "/v1/novacodepro/releases"),
    "deployment": ("/health", "/ready", "/metrics", "/v1/novacodepro/deployments"),
    "marketplace": ("/health", "/ready", "/metrics", "/v1/novacodepro/marketplace"),
    "observability": ("/health", "/ready", "/metrics", "/v1/novacodepro/operations", "/v1/novacodepro/sre"),
    "sre": ("/health", "/ready", "/metrics", "/v1/novacodepro/operations", "/v1/novacodepro/sre"),
    "incident": ("/health", "/ready", "/metrics", "/v1/novacodepro/operations/incidents", "/v1/novacodepro/operations/maintenance-windows", "/v1/novacodepro/operations/backups"),
    "command-center": ("/health", "/ready", "/metrics", "/v1/novacodepro/executive/command-center", "/v1/novacodepro/executive/briefings"),
    "executive": ("/health", "/ready", "/metrics", "/v1/novacodepro/executive"),
    "board-governance": ("/health", "/ready", "/metrics", "/v1/novacodepro/board"),
    "board": ("/health", "/ready", "/metrics", "/v1/novacodepro/board"),
    "audit": ("/health", "/ready", "/metrics", "/v1/novacodepro/audit", "/v1/novacodepro/events"),
    "event-mesh": ("/health", "/ready", "/metrics", "/v1/novacodepro/audit", "/v1/novacodepro/events"),
    "notification": ("/health", "/ready", "/metrics"),
}


class ServiceBoundaryMiddleware:
    def __init__(self, app, *, service_name: str):
        self.app = app
        self.service_name = service_name
        self.allowed_prefixes = SERVICE_ROUTE_ALLOWLIST.get(service_name, ("/health", "/ready", "/metrics"))

    def _allowed(self, path: str) -> bool:
        if path in {"/docs", "/redoc", "/openapi.json"}:
            return True
        for prefix in self.allowed_prefixes:
            if path == prefix.rstrip("/"):
                return True
            if prefix.endswith("/") and path.startswith(prefix):
                return True
            if path.startswith(prefix + "/"):
                return True
        return False

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        path = str(scope.get("path") or "")
        if not self._allowed(path):
            response = JSONResponse({"detail": "route_not_owned"}, status_code=404)
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


def _metrics_text(service: NovaCodeProPlatform) -> str:
    status = service.status()
    return "\n".join(
        [
            f"novacodepro_service_status{{service=\"{status['service']}\"}} 1",
            f"novacodepro_workflows_total {status.get('workflow_count', 0)}",
            f"novacodepro_solutions_total {status.get('solution_count', 0)}",
            f"novacodepro_agents_total {status.get('agent_registry_count', 0)}",
            f"novacodepro_outbox_pending_total {len(service.repository.list_outbox(limit=1000))}",
        ]
    )


def build_process_app(*, service_name: str, db_env_var: str, title: str | None = None, async_agents: bool = False) -> FastAPI:
    service_definition = get_service_definition(service_name)
    db_path = _db_path_from_env(db_env_var, service_name)
    database_url = os.environ.get(service_definition.database_url_env_var) or os.environ.get("NOVACODEPRO_DATABASE_URL")
    platform = get_novacodepro_platform(db_path, database_url=database_url)
    platform.default_agent_async_execution = async_agents
    broker = build_durable_event_broker(platform.repository)
    outbox_worker = OutboxWorker(platform=platform, broker=broker)
    agent_worker = AgentExecutionWorker(platform=platform)

    app = FastAPI(title=title or f"NovaCodePro {service_name}")
    app.add_middleware(ServiceBoundaryMiddleware, service_name=service_name)
    app.add_middleware(DistributedTracingMiddleware)
    if service_name == "gateway":
        app.include_router(build_auth_router())
    app.include_router(build_novacodepro_platform_router(platform))
    if service_name == "workflow":
        app.include_router(build_novacodepro_workflow_fabric_router(WorkflowFabricService(platform)))
    if service_name == "solution":
        app.include_router(build_solution_engineering_router())

    @app.get("/health")
    def health() -> dict[str, Any]:
        state = platform.status()
        return {
            "service": service_name,
            "status": "healthy",
            "db_path": str(db_path),
            "outbox_pending": len(platform.repository.list_outbox(limit=1000)),
            "agent_pending": len(platform.pending_agent_executions(limit=1000)),
            "platform_health": state.get("platform_health", "healthy"),
            "route_allowlist": SERVICE_ROUTE_ALLOWLIST.get(service_name, ("/health", "/ready", "/metrics")),
        }

    @app.get("/ready")
    def ready() -> dict[str, Any]:
        return {"service": service_name, "ready": True}

    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics() -> str:
        return _metrics_text(platform)

    @app.get("/v1/outbox")
    def outbox() -> list[dict[str, Any]]:
        return platform.repository.list_outbox(limit=200)

    @app.post("/v1/outbox/drain")
    def drain_outbox() -> dict[str, int]:
        return outbox_worker.run_once()

    @app.post("/v1/workers/agents/drain")
    def drain_agent_queue() -> dict[str, int]:
        return agent_worker.run_once()

    @app.post("/v1/outbox/{event_id}/ack")
    def ack_outbox(event_id: str) -> dict[str, Any]:
        platform.repository.ack_outbox_event(event_id)
        return {"event_id": event_id, "status": "published"}

    @app.post("/v1/outbox/{event_id}/fail")
    def fail_outbox(event_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        platform.repository.fail_outbox_event(event_id, str((payload or {}).get("error") or "failed"))
        return {"event_id": event_id, "status": "failed"}

    app.state.platform = platform
    app.state.broker = broker
    app.state.outbox_worker = outbox_worker
    app.state.agent_worker = agent_worker
    app.state.service_definition = service_definition
    app.state.service_name = service_name
    return app
