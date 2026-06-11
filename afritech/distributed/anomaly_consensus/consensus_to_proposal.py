from __future__ import annotations

from afritech.extensions.afriprog.copilot_assist import generate_context_aware_proposal


def consensus_to_proposal(consensus: dict[str, object]):
    return generate_context_aware_proposal(
        intent=f"Investigate global anomaly consensus: {consensus.get('anomaly_type')}",
        affected_files=("distributed_anomaly_context",),
        from_failure=str(consensus.get("anomaly_type", "global anomaly")),
    )


__all__ = ["consensus_to_proposal"]
