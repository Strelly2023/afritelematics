from __future__ import annotations

import sys

from afritech.distributed.anomaly_consensus import collect_evidence, observe_anomaly

VALIDATOR_NAME = "afritech.ci.afriprog_evidence_integrity_validator"


def validate() -> None:
    good = observe_anomaly(
        node_id="node-A",
        timestamp="2026-06-06T00:00:00Z",
        anomaly_type="contract_mismatch",
        severity="HIGH",
        context_hash="ctx",
    )
    bad = {**good, "signature": "bad"}
    evidence = collect_evidence((good, bad))
    if len(evidence["verified_reports"]) != 1:
        raise RuntimeError("valid signed evidence must be accepted")
    if len(evidence["rejected_reports"]) != 1:
        raise RuntimeError("invalid signed evidence must be rejected")


def main() -> int:
    try:
        validate()
        print("Afriprog evidence integrity validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog evidence integrity validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
