"""Runtime state recovery helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RecoveryOutcome:
    product_code: str
    status: str
    details: dict[str, Any]

