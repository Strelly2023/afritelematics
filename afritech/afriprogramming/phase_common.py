"""Shared helpers for NovaRide phase projection modules."""

from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
from typing import Any

from afritech.afriprogramming.phase_common import DEFAULT_ORGANIZATION_ID, build_audit_log, build_control_projection, get_phase_store, phase_now


def get_phase_store():
    return get_platform_store()


def phase_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def build_audit_log(organization_id: str | None = None) -> dict[str, Any]:
    entries = get_phase_store().list_audit_events(organization_id=organization_id, limit=500)
    return {
        "view": "novaprogramming_audit_log",
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "entries": entries,
        "count": len(entries),
        "read_only": True,
    }


def build_control_projection(name: str, *args: Any, **kwargs: Any) -> Any:
    control_plane = import_module("afritech.afriprogramming.control_plane")
    return getattr(control_plane, name)(*args, **kwargs)
