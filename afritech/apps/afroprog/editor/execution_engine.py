"""Execution preview for AfriPro generated code.

The engine is intentionally non-authoritative. It previews how code would be
validated, not how it would mutate runtime.
"""

from __future__ import annotations


def preview_execution(code: str) -> dict[str, object]:
    return {
        "mode": "preview_only",
        "line_count": len(code.splitlines()),
        "sandboxed": True,
        "mutation_allowed": False,
        "next_step": "send_to_governance",
    }


__all__ = ["preview_execution"]
