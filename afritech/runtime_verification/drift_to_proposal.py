from __future__ import annotations

from afritech.extensions.afriprog.copilot_assist import generate_context_aware_proposal


def drift_to_proposal(
    drift: dict[str, object],
    context: dict[str, object],
):
    return generate_context_aware_proposal(
        intent=f"Investigate contract drift: {drift.get('type')}",
        affected_files=tuple(context.get("affected_files", ())),
        from_failure=str(drift.get("type", "contract drift")),
    )


__all__ = ["drift_to_proposal"]
