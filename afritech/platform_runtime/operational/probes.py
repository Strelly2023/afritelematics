"""Real verification probes for runtime operationalization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol
from urllib.parse import urlparse

import asyncio
import httpx

from ..adapters.base import AdapterExecutionMode


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class VerificationContext:
    base_url: str
    product_code: str
    product_version: str
    environment: str
    region: str
    token: str | None = None
    tenant_id: str = ""
    approval_id: str = ""
    deployment_id: str = ""


@dataclass(frozen=True, slots=True)
class VerificationProbeResult:
    probe_id: str
    status: str
    started_at: str
    completed_at: str
    duration_ms: float
    attempts: int
    evidence: dict[str, Any]
    error_code: str | None = None
    error_message: str | None = None


class VerificationProbe(Protocol):
    probe_id: str
    category: str
    required: bool

    async def execute(self, context: VerificationContext) -> VerificationProbeResult: ...


@dataclass(frozen=True, slots=True)
class HttpProbe:
    probe_id: str
    category: str
    path: str
    expected_status: int = 200
    required: bool = True

    async def execute(self, context: VerificationContext) -> VerificationProbeResult:
        started = datetime.now(timezone.utc)
        headers = {"Authorization": f"Bearer {context.token}"} if context.token else {}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(context.base_url.rstrip("/") + self.path, headers=headers)
        status = "PASS" if resp.status_code == self.expected_status else "FAIL"
        return VerificationProbeResult(self.probe_id, status, started.isoformat(), _now(), (datetime.now(timezone.utc) - started).total_seconds() * 1000.0, 1, {"status_code": resp.status_code, "path": self.path}, None if status == "PASS" else "unexpected_status", None if status == "PASS" else resp.text[:200])


@dataclass(frozen=True, slots=True)
class SyntheticCommandProbe:
    probe_id: str
    category: str = "Synthetic command"
    required: bool = True

    async def execute(self, context: VerificationContext) -> VerificationProbeResult:
        started = datetime.now(timezone.utc)
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                context.base_url.rstrip("/") + "/v1/platform/runtime/products/novafleet/commands/RegisterFleetVehicle",
                headers={"Authorization": f"Bearer {context.token}"} if context.token else {},
                json={
                    "payload": {"payload": {"vehicle_id": "synthetic-vehicle"}},
                    "context": {
                        "request_id": f"verification-{context.product_code}",
                        "correlation_id": f"verification-{context.product_code}",
                        "tenant_id": context.tenant_id or "verification-tenant",
                        "organization_id": "novatech",
                        "actor_id": "verification",
                        "actor_type": "system",
                        "environment": context.environment,
                        "region": context.region,
                        "language": "en",
                        "timezone": "UTC",
                        "trace_id": f"trace-{context.product_code}",
                        "purpose": "verification",
                    },
                },
            )
        status = "PASS" if resp.status_code < 400 else "FAIL"
        return VerificationProbeResult(self.probe_id, status, started.isoformat(), _now(), (datetime.now(timezone.utc) - started).total_seconds() * 1000.0, 1, {"status_code": resp.status_code, "response": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text[:200]}, None if status == "PASS" else "synthetic_command_failed", None if status == "PASS" else resp.text[:200])


def build_reference_probes(product_code: str) -> tuple[VerificationProbe, ...]:
    return (
        HttpProbe(f"{product_code}:health", "Platform", "/health/live"),
        HttpProbe(f"{product_code}:ready", "Platform", "/health/ready"),
        HttpProbe(f"{product_code}:products", "Platform", "/health/products"),
        HttpProbe(f"{product_code}:workers", "Platform", "/health/workers"),
        HttpProbe(f"{product_code}:platform", "Platform", "/v1/platform"),
        SyntheticCommandProbe(f"{product_code}:synthetic-command"),
    )

