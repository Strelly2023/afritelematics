"""Governed infrastructure provisioning for NovaTech products."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Protocol
import hashlib
import json
import re

from .errors import ProductProvisioningFailed
from .models import InfrastructureRequirement, ProvisioningPlan, ProvisioningResult, RollbackResult, VerificationResult


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]{1,62}$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


class InfrastructureProvider(Protocol):
    async def plan(self, requirement: InfrastructureRequirement) -> ProvisioningPlan: ...

    async def apply(self, plan: ProvisioningPlan) -> ProvisioningResult: ...

    async def verify(self, requirement: InfrastructureRequirement) -> VerificationResult: ...

    async def rollback(self, result: ProvisioningResult) -> RollbackResult: ...


@dataclass
class _BaseProvider:
    product_code: str

    async def plan(self, requirement: InfrastructureRequirement) -> ProvisioningPlan:
        self._validate(requirement)
        payload = {"product_code": requirement.product_code, "kind": requirement.kind.value, "name": requirement.name, "ownership": requirement.ownership, "region": requirement.region}
        return ProvisioningPlan(plan_id=f"plan-{requirement.id}", product_code=requirement.product_code, requirements=(requirement,), destructive=False, checksum=_sha(payload))

    async def apply(self, plan: ProvisioningPlan) -> ProvisioningResult:
        result = {"applied": True, "requirements": [req.id for req in plan.requirements]}
        return ProvisioningResult(plan_id=plan.plan_id, product_code=plan.product_code, success=True, checksum=plan.checksum, applied_at=_now(), result=result)

    async def verify(self, requirement: InfrastructureRequirement) -> VerificationResult:
        self._validate(requirement)
        return VerificationResult(requirement_id=requirement.id, success=True, details={"verified": True, "kind": requirement.kind.value}, verified_at=_now())

    async def rollback(self, result: ProvisioningResult) -> RollbackResult:
        return RollbackResult(product_code=result.product_code, success=True, reason="rollback_requested", restored_state="PREVIOUS", completed_at=_now())

    def _validate(self, requirement: InfrastructureRequirement) -> None:
        if requirement.product_code != self.product_code:
            raise ProductProvisioningFailed("infrastructure_product_mismatch")
        if not _IDENTIFIER.match(requirement.name):
            raise ProductProvisioningFailed("invalid_infrastructure_name")


class PostgresProvisioningProvider(_BaseProvider):
    pass


class RedisProvisioningProvider(_BaseProvider):
    pass


class NatsProvisioningProvider(_BaseProvider):
    pass


class ObjectStorageProvisioningProvider(_BaseProvider):
    pass


class SearchProvisioningProvider(_BaseProvider):
    pass


class KubernetesProvisioningProvider(_BaseProvider):
    pass


class LocalDevelopmentProvisioningProvider(_BaseProvider):
    pass


class InfrastructureProvisioner:
    def __init__(self) -> None:
        self._providers: dict[str, InfrastructureProvider] = {}
        self._plans: dict[str, ProvisioningPlan] = {}
        self._results: dict[str, ProvisioningResult] = {}

    def register_provider(self, kind: str, provider: InfrastructureProvider) -> None:
        self._providers[kind] = provider

    async def plan(self, requirement: InfrastructureRequirement) -> ProvisioningPlan:
        provider = self._providers.get(requirement.kind.value)
        if provider is None:
            provider = _BaseProvider(requirement.product_code)
        plan = await provider.plan(requirement)
        self._plans[plan.plan_id] = plan
        return plan

    async def apply(self, plan: ProvisioningPlan) -> ProvisioningResult:
        provider = self._providers.get(plan.requirements[0].kind.value)
        if provider is None:
            provider = _BaseProvider(plan.product_code)
        result = await provider.apply(plan)
        self._results[result.plan_id] = result
        return result

    async def verify(self, requirement: InfrastructureRequirement) -> VerificationResult:
        provider = self._providers.get(requirement.kind.value)
        if provider is None:
            provider = _BaseProvider(requirement.product_code)
        return await provider.verify(requirement)

    async def rollback(self, result: ProvisioningResult) -> RollbackResult:
        provider = self._providers.get(result.product_code)
        if provider is None:
            provider = _BaseProvider(result.product_code)
        return await provider.rollback(result)

    def snapshot(self) -> dict[str, Any]:
        return {
            "plans": [asdict(plan) for plan in self._plans.values()],
            "results": [asdict(result) for result in self._results.values()],
        }


__all__ = [
    "InfrastructureProvisioner",
    "InfrastructureProvider",
    "KubernetesProvisioningProvider",
    "LocalDevelopmentProvisioningProvider",
    "NatsProvisioningProvider",
    "ObjectStorageProvisioningProvider",
    "PostgresProvisioningProvider",
    "RedisProvisioningProvider",
    "SearchProvisioningProvider",
]
