from __future__ import annotations

import sys

from afritech.distributed.anomaly_consensus import compute_consensus, observe_anomaly

VALIDATOR_NAME = "afritech.ci.afriprog_consensus_non_authority_validator"


def validate() -> None:
    reports = (
        observe_anomaly(
            node_id="node-A",
            timestamp="2026-06-06T00:00:00Z",
            anomaly_type="contract_mismatch",
            severity="HIGH",
            context_hash="ctx",
        ),
        observe_anomaly(
            node_id="node-B",
            timestamp="2026-06-06T00:00:01Z",
            anomaly_type="contract_mismatch",
            severity="HIGH",
            context_hash="ctx",
        ),
    )
    consensus = compute_consensus(reports, total_nodes=2, min_quorum=2)[0]
    if consensus["consensus_authority"] != "non_authoritative":
        raise RuntimeError("consensus must remain non-authoritative")
    if consensus["runtime_mutation_allowed"] is not False:
        raise RuntimeError("consensus must not mutate runtime")


def main() -> int:
    try:
        validate()
        print("Afriprog consensus non-authority validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog consensus non-authority validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
