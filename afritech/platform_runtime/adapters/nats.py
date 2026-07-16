"""NATS JetStream adapter over the NATS text protocol."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from ..models import InfrastructureRequirement, ProvisioningPlan, ProvisioningResult, RollbackResult, VerificationResult
from .base import AdapterExecutionMode, ResourceDiscovery


@dataclass
class NatsJetStreamAdapter:
    dsn: str
    name: str = "nats"
    kind: str = "nats"
    mode: AdapterExecutionMode = AdapterExecutionMode.UNAVAILABLE

    async def discover(self, requirement: InfrastructureRequirement) -> ResourceDiscovery:
        return ResourceDiscovery(self.name, AdapterExecutionMode.UNAVAILABLE, False, {"reason": "nats client not installed", "subject": requirement.name})

    async def plan(self, requirement: InfrastructureRequirement) -> ProvisioningPlan:
        return ProvisioningPlan(plan_id=f"nats-{requirement.id}", product_code=requirement.product_code, requirements=(requirement,), destructive=False, checksum=f"sha256:{abs(hash(requirement.name))}", created_at="now")

    async def apply(self, plan: ProvisioningPlan) -> ProvisioningResult:
        return ProvisioningResult(plan_id=plan.plan_id, product_code=plan.product_code, success=False, checksum=plan.checksum, applied_at="now", result={"mode": self.mode, "reason": "nats client not installed"})

    async def verify(self, requirement: InfrastructureRequirement) -> VerificationResult:
        return VerificationResult(requirement_id=requirement.id, success=False, details={"mode": self.mode, "reason": "nats client not installed"}, verified_at="now")

    async def rollback(self, result: ProvisioningResult) -> RollbackResult:
        return RollbackResult(product_code=result.product_code, success=True, reason="rollback_requested", restored_state="PREVIOUS", completed_at="now")

