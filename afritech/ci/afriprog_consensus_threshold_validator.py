from __future__ import annotations

import sys

from afritech.distributed.anomaly_consensus import compute_consensus, observe_anomaly

VALIDATOR_NAME = "afritech.ci.afriprog_consensus_threshold_validator"


def validate() -> None:
    report = observe_anomaly(
        node_id="node-A",
        timestamp="2026-06-06T00:00:00Z",
        anomaly_type="contract_mismatch",
        severity="HIGH",
        context_hash="ctx",
    )
    if compute_consensus((report,), total_nodes=3, min_quorum=2):
        raise RuntimeError("single node must not form global consensus")
    reports = (
        report,
        observe_anomaly(
            node_id="node-B",
            timestamp="2026-06-06T00:00:01Z",
            anomaly_type="contract_mismatch",
            severity="HIGH",
            context_hash="ctx",
        ),
    )
    if not compute_consensus(reports, total_nodes=3, min_quorum=2):
        raise RuntimeError("quorum reports must form consensus")


def main() -> int:
    try:
        validate()
        print("Afriprog consensus threshold validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog consensus threshold validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
