"""Result model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class RuntimeResult:
    status: str
    data: dict[str, Any] = field(default_factory=dict)
    events: tuple[dict[str, Any], ...] = ()
    correlation_id: str | None = None
