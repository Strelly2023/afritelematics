"""Shared AfriProgramming audit helpers.

This module must not import control_plane or phase modules.
"""

from __future__ import annotations

from typing import Any


def build_audit_log(
    *,
    phase: str,
    action: str,
    actor: str = "system",
    status: str = "recorded",
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "phase": phase,
        "action": action,
        "actor": actor,
        "status": status,
        "evidence": evidence or {},
    }
