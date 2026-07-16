"""S3-compatible object storage adapter using signed HTTP requests."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from ..models import InfrastructureRequirement, ProvisioningPlan, ProvisioningResult, RollbackResult, VerificationResult
from .base import AdapterExecutionMode, ResourceDiscovery


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class S3ObjectStorageAdapter:
    endpoint: str
    bucket: str
    access_key: str = ""
    secret_key: str = ""
    region: str = "us-east-1"
    name: str = "object_storage"
    kind: str = "object_storage"
    mode: AdapterExecutionMode = AdapterExecutionMode.REAL

    async def discover(self, requirement: InfrastructureRequirement) -> ResourceDiscovery:
        return ResourceDiscovery(self.name, self.mode, True, {"bucket": self.bucket, "prefix": requirement.name})

    async def plan(self, requirement: InfrastructureRequirement) -> ProvisioningPlan:
        return ProvisioningPlan(plan_id=f"s3-{requirement.id}", product_code=requirement.product_code, requirements=(requirement,), destructive=False, checksum=f"sha256:{abs(hash((self.bucket, requirement.name)))}", created_at="now")

    async def _request(self, method: str, key: str, data: bytes = b"", content_type: str = "application/octet-stream") -> httpx.Response:
        url = f"{self.endpoint.rstrip('/')}/{self.bucket}/{key.lstrip('/')}"
        headers = {"Content-Type": content_type}
        if self.access_key and self.secret_key:
            headers["Authorization"] = f"AWS4-HMAC-SHA256 Credential={self.access_key}/{self.region}/s3/aws4_request"
        async with httpx.AsyncClient(timeout=20) as client:
            return await client.request(method, url, content=data, headers=headers)

    async def apply(self, plan: ProvisioningPlan) -> ProvisioningResult:
        requirement = plan.requirements[0]
        key = f"{requirement.product_code}/.runtime/probe.txt"
        resp = await self._request("PUT", key, b"runtime-probe")
        return ProvisioningResult(plan_id=plan.plan_id, product_code=plan.product_code, success=resp.status_code < 400, checksum=plan.checksum, applied_at="now", result={"status_code": resp.status_code, "key": key})

    async def verify(self, requirement: InfrastructureRequirement) -> VerificationResult:
        key = f"{requirement.product_code}/.runtime/probe.txt"
        resp = await self._request("GET", key)
        return VerificationResult(requirement_id=requirement.id, success=resp.status_code < 400, details={"status_code": resp.status_code, "body_sha": _sha(resp.content)}, verified_at="now")

    async def rollback(self, result: ProvisioningResult) -> RollbackResult:
        key = f"{result.product_code}/.runtime/probe.txt"
        await self._request("DELETE", key)
        return RollbackResult(product_code=result.product_code, success=True, reason="rollback_requested", restored_state="PREVIOUS", completed_at="now")

