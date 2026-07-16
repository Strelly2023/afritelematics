"""Restart recovery helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    product_code: str
    status: str
    details: dict[str, Any]


class RecoveryRunner:
    async def recover(self, product_code: str, *, observed_state: dict[str, Any]) -> RecoveryResult:
        return RecoveryResult(product_code=product_code, status="RECOVERED" if observed_state else "MANUAL_INTERVENTION_REQUIRED", details=observed_state)

