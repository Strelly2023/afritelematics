from __future__ import annotations

import sys

from afritech.runtime_monitoring import build_anomaly_context

VALIDATOR_NAME = "afritech.ci.afriprog_anomaly_context_integrity_validator"


def validate() -> None:
    context = build_anomaly_context(
        {"type": "contract_mismatch"},
        timestamp="2026-06-06T00:00:00Z",
        event_trace=("RideRequested",),
        current_receipt="v1",
        expected_receipt="v2",
        affected_files=("afritech/api/driver.py",),
        validator_failures=("driver_contract_replay_validator",),
    )
    if len(context["context_hash"]) != 64:
        raise RuntimeError("anomaly context must be hash-bound")
    if context["replay_sufficient"] is not True:
        raise RuntimeError("anomaly context must be replay-sufficient")
    if context["runtime_mutation_allowed"] is not False:
        raise RuntimeError("anomaly context must not mutate runtime")


def main() -> int:
    try:
        validate()
        print("Afriprog anomaly context integrity validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog anomaly context integrity validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
