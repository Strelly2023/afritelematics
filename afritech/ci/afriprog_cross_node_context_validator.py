from __future__ import annotations

import sys

from afritech.distributed.anomaly_consensus import compute_consensus, observe_anomaly

VALIDATOR_NAME = "afritech.ci.afriprog_cross_node_context_validator"


def validate() -> None:
    reports = (
        observe_anomaly(
            node_id="node-A",
            timestamp="2026-06-06T00:00:00Z",
            anomaly_type="contract_mismatch",
            severity="HIGH",
            context_hash="ctx-1",
        ),
        observe_anomaly(
            node_id="node-B",
            timestamp="2026-06-06T00:00:01Z",
            anomaly_type="contract_mismatch",
            severity="HIGH",
            context_hash="ctx-2",
        ),
    )
    if compute_consensus(reports, total_nodes=2, min_quorum=2):
        raise RuntimeError("different contexts must not form one consensus")


def main() -> int:
    try:
        validate()
        print("Afriprog cross-node context validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog cross-node context validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
