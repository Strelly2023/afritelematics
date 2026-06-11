"""Codex-style dashboard views for AfriPro."""

from __future__ import annotations

from .workspace import build_workspace_payload


def render_afroprog_dashboard_view() -> dict[str, object]:
    payload = build_workspace_payload()
    return {
        "view": "afroprog_dashboard",
        "payload": payload,
        "read_only": True,
        "proposal_only": True,
        "creates_authority": False,
        "validates_truth": False,
        "executes_runtime": False,
    }


__all__ = ["render_afroprog_dashboard_view"]
