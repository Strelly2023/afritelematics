from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from afritech.api.realtime.ws_server import WebSocketHub


dashboard_hub = WebSocketHub()


async def publish_dashboard_event(
    event_type: str,
    data: Mapping[str, Any],
) -> dict[str, Any]:
    return await dashboard_hub.publish_event("dashboard", event_type, data)


async def publish_dashboard_snapshot(data: Mapping[str, Any]) -> dict[str, Any]:
    return await publish_dashboard_event("DASHBOARD_SNAPSHOT", data)

