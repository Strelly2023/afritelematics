"""WebSocket runtime helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class WebSocketSession:
    channel_id: str
    product_code: str
    connected: bool
    metadata: dict[str, Any]
