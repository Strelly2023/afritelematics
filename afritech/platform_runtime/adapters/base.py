"""Adapter contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

from ..models import InfrastructureRequirement, ProvisioningPlan, ProvisioningResult, RollbackResult, VerificationResult


class AdapterExecutionMode(StrEnum):
    REAL = "REAL"
    SIMULATED = "SIMULATED"
    DRY_RUN = "DRY_RUN"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class ResourceDiscovery:
    adapter: str
    mode: AdapterExecutionMode
    discovered: bool
    details: dict[str, Any]


class OperationalAdapter(Protocol):
    name: str
    kind: str

    async def discover(self, requirement: InfrastructureRequirement) -> ResourceDiscovery: ...
    async def plan(self, requirement: InfrastructureRequirement) -> ProvisioningPlan: ...
    async def apply(self, plan: ProvisioningPlan) -> ProvisioningResult: ...
    async def verify(self, requirement: InfrastructureRequirement) -> VerificationResult: ...
    async def rollback(self, result: ProvisioningResult) -> RollbackResult: ...

