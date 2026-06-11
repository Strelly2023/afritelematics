from __future__ import annotations

import sys

from afritech.runtime_monitoring import validate_monitoring_pipeline

VALIDATOR_NAME = "afritech.ci.afriprog_runtime_monitoring_validator"


def validate() -> None:
    result = validate_monitoring_pipeline()
    if result["anomaly_count"] != 1:
        raise RuntimeError("runtime monitoring must detect anomaly")
    if result["governance_required"] is not True:
        raise RuntimeError("runtime monitoring proposal must require governance")


def main() -> int:
    try:
        validate()
        print("Afriprog runtime monitoring validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog runtime monitoring validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
