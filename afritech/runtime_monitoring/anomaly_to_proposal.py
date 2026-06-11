from __future__ import annotations

from afritech.extensions.afriprog.copilot_assist import (
    generate_context_aware_proposal,
)


def anomaly_to_proposal(
    anomaly: dict[str, object],
    context: dict[str, object],
):
    proposal = generate_context_aware_proposal(
        intent=f"Investigate runtime anomaly: {anomaly.get('type')}",
        affected_files=tuple(context.get("affected_files", ())),
        from_failure=str(anomaly.get("type", "runtime anomaly")),
    )
    return proposal


__all__ = ["anomaly_to_proposal"]
