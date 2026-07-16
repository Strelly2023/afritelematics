"""Redis adapter with raw RESP protocol to avoid extra dependencies."""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from ..errors import ProductProvisioningFailed
from ..models import InfrastructureRequirement, ProvisioningPlan, ProvisioningResult, RollbackResult, VerificationResult
from .base import AdapterExecutionMode, ResourceDiscovery


def _encode(parts: list[str]) -> bytes:
    buf = [f"*{len(parts)}\r\n".encode()]
    for part in parts:
        raw = part.encode()
        buf.append(f"${len(raw)}\r\n".encode())
        buf.append(raw + b"\r\n")
    return b"".join(buf)


async def _send(host: str, port: int, parts: list[str]) -> bytes:
    reader, writer = await asyncio.open_connection(host, port)
    writer.write(_encode(parts))
    await writer.drain()
    data = await reader.read(4096)
    writer.close()
    try:
        await writer.wait_closed()
    except Exception:
        pass
    return data


@dataclass
class RedisAdapter:
    dsn: str
    name: str = "redis"
    kind: str = "redis"
    mode: AdapterExecutionMode = AdapterExecutionMode.REAL

    def _target(self):
        parsed = urlparse(self.dsn)
        return parsed.hostname or "127.0.0.1", parsed.port or 6379, (parsed.path or "/0").lstrip("/")

    async def discover(self, requirement: InfrastructureRequirement) -> ResourceDiscovery:
        host, port, db = self._target()
        try:
            pong = await _send(host, port, ["PING"])
            return ResourceDiscovery(self.name, self.mode, True, {"pong": pong.decode(errors="ignore"), "db": db, "namespace": requirement.name})
        except Exception as exc:
            return ResourceDiscovery(self.name, AdapterExecutionMode.UNAVAILABLE, False, {"error": str(exc)})

    async def plan(self, requirement: InfrastructureRequirement) -> ProvisioningPlan:
        return ProvisioningPlan(plan_id=f"redis-{requirement.id}", product_code=requirement.product_code, requirements=(requirement,), destructive=False, checksum=f"sha256:{abs(hash(requirement.name))}", created_at="now")

    async def apply(self, plan: ProvisioningPlan) -> ProvisioningResult:
        requirement = plan.requirements[0]
        host, port, db = self._target()
        await _send(host, port, ["SET", f"{requirement.name}:health:probe", "1", "EX", "60"])
        return ProvisioningResult(plan_id=plan.plan_id, product_code=plan.product_code, success=True, checksum=plan.checksum, applied_at="now", result={"real": True, "namespace": requirement.name, "db": db})

    async def verify(self, requirement: InfrastructureRequirement) -> VerificationResult:
        host, port, db = self._target()
        await _send(host, port, ["SET", f"{requirement.name}:verification", "1", "EX", "5"])
        data = await _send(host, port, ["GET", f"{requirement.name}:verification"])
        return VerificationResult(requirement_id=requirement.id, success=b"1" in data, details={"db": db, "raw": data.decode(errors="ignore")}, verified_at="now")

    async def rollback(self, result: ProvisioningResult) -> RollbackResult:
        host, port, _ = self._target()
        await _send(host, port, ["DEL", f"{result.product_code}:verification"])
        return RollbackResult(product_code=result.product_code, success=True, reason="rollback_requested", restored_state="PREVIOUS", completed_at="now")

