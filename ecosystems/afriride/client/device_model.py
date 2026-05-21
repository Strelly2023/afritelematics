from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MobileEvent:
    device_id: str
    event_id: str
    local_timestamp: int
    payload: dict[str, Any]
