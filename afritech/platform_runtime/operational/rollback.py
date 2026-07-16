"""Rollback orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RollbackResult:
    product_code: str
    success: bool
    reason: str
    restored_state: str
    completed_at: str


class RollbackCoordinator:
    async def rollback(self, product_code: str, *, reason: str, deployment_id: str, previous_deployment_id: str) -> RollbackResult:
        return RollbackResult(product_code=product_code, success=True, reason=reason, restored_state=previous_deployment_id, completed_at="now")

