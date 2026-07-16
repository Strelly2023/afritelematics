"""Worker orchestration API for NovaTech executable product runtime."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.platform_runtime.worker_supervisor import WorkerSupervisor


class WorkerActionPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    reason: str = ""


def _service(service: WorkerSupervisor | None = None) -> WorkerSupervisor:
    return service or WorkerSupervisor()


def build_runtime_worker_router(service: WorkerSupervisor | None = None) -> APIRouter:
    router = APIRouter(prefix="/v1/platform/runtime/workers", tags=["platform-runtime-workers"])
    supervisor = _service(service)

    @router.get("")
    def health(_: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return supervisor.health_snapshot()

    @router.get("/{product_code}")
    def product_health(product_code: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return {"product_code": product_code, "health": [supervisor.worker_health(product_code, worker.name) for worker in supervisor.worker_registry.list_product_workers(product_code)]}

    @router.get("/{product_code}/{worker_name}")
    def worker_health(product_code: str, worker_name: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return supervisor.worker_health(product_code, worker_name)

    @router.post("/{product_code}/start")
    async def start(product_code: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        return asdict(await supervisor.start_product_workers(product_code))

    @router.post("/{product_code}/stop")
    async def stop(product_code: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        return asdict(await supervisor.stop_product_workers(product_code))

    @router.post("/{product_code}/{worker_name}/pause")
    async def pause(product_code: str, worker_name: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        return asdict(await supervisor.pause_worker(product_code, worker_name))

    @router.post("/{product_code}/{worker_name}/resume")
    async def resume(product_code: str, worker_name: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        return asdict(await supervisor.resume_worker(product_code, worker_name))

    @router.post("/{product_code}/{worker_name}/restart")
    async def restart(product_code: str, worker_name: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        return asdict(await supervisor.restart_worker(product_code, worker_name))

    return router


__all__ = ["build_runtime_worker_router"]
