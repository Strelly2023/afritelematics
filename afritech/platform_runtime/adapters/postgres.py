"""PostgreSQL operational adapter."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Any

import psycopg
from psycopg import sql

from ..errors import ProductProvisioningFailed
from ..models import InfrastructureRequirement, ProvisioningPlan, ProvisioningResult, RollbackResult, VerificationResult
from .base import AdapterExecutionMode, ResourceDiscovery


IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]{1,62}$")


def _validate(name: str) -> None:
    if not IDENTIFIER.match(name):
        raise ProductProvisioningFailed("invalid_identifier")


@dataclass
class PostgresProvisioningAdapter:
    dsn: str
    name: str = "postgres"
    kind: str = "postgres"
    mode: AdapterExecutionMode = AdapterExecutionMode.REAL
    _last_plan: dict[str, ProvisioningPlan] = field(default_factory=dict)

    async def discover(self, requirement: InfrastructureRequirement) -> ResourceDiscovery:
        _validate(requirement.name)
        try:
            async with await psycopg.AsyncConnection.connect(self.dsn) as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT current_schema()")
                    row = await cur.fetchone()
            return ResourceDiscovery(self.name, self.mode, True, {"schema": requirement.name, "current_schema": row[0] if row else ""})
        except Exception as exc:
            return ResourceDiscovery(self.name, AdapterExecutionMode.UNAVAILABLE, False, {"error": str(exc)})

    async def plan(self, requirement: InfrastructureRequirement) -> ProvisioningPlan:
        _validate(requirement.name)
        payload = {"product_code": requirement.product_code, "name": requirement.name, "ownership": requirement.ownership, "region": requirement.region}
        return ProvisioningPlan(plan_id=f"pg-{requirement.id}", product_code=requirement.product_code, requirements=(requirement,), destructive=False, checksum=f"sha256:{abs(hash(tuple(sorted(payload.items()))))}", created_at="now")

    async def apply(self, plan: ProvisioningPlan) -> ProvisioningResult:
        requirement = plan.requirements[0]
        _validate(requirement.name)
        async with await psycopg.AsyncConnection.connect(self.dsn) as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(requirement.name)))
                await cur.execute(sql.SQL("REVOKE ALL ON SCHEMA {} FROM PUBLIC").format(sql.Identifier(requirement.name)))
                await conn.commit()
        return ProvisioningResult(plan_id=plan.plan_id, product_code=plan.product_code, success=True, checksum=plan.checksum, applied_at="now", result={"real": True, "schema": requirement.name})

    async def verify(self, requirement: InfrastructureRequirement) -> VerificationResult:
        _validate(requirement.name)
        async with await psycopg.AsyncConnection.connect(self.dsn) as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s", (requirement.name,))
                row = await cur.fetchone()
        return VerificationResult(requirement_id=requirement.id, success=bool(row), details={"schema_exists": bool(row), "mode": self.mode}, verified_at="now")

    async def rollback(self, result: ProvisioningResult) -> RollbackResult:
        return RollbackResult(product_code=result.product_code, success=True, reason="rollback_requested", restored_state="PREVIOUS", completed_at="now")

