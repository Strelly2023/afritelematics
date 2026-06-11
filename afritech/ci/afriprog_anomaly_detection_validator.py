from __future__ import annotations

import sys

from afritech.runtime_monitoring import collect_runtime_events, detect_anomalies

VALIDATOR_NAME = "afritech.ci.afriprog_anomaly_detection_validator"


def validate() -> None:
    events = collect_runtime_events(
        validation_failures=("validator failed",),
        contract_mismatches=("receipt mismatch",),
    )
    anomalies = detect_anomalies(events)
    if {anomaly["type"] for anomaly in anomalies} != {
        "validation_failure",
        "contract_mismatch",
    }:
        raise RuntimeError("anomaly detector did not emit expected anomalies")
    if events["runtime_mutation_allowed"] is not False:
        raise RuntimeError("runtime monitoring must not mutate runtime")


def main() -> int:
    try:
        validate()
        print("Afriprog anomaly detection validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog anomaly detection validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
