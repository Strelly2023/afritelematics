from __future__ import annotations

import sys

from afritech.distributed.anomaly_consensus.consensus_validators import (
    validate_consensus_pipeline,
)

VALIDATOR_NAME = "afritech.ci.afriprog_global_anomaly_consensus_validator"


def validate() -> None:
    result = validate_consensus_pipeline()
    if result["consensus_count"] != 1:
        raise RuntimeError("global anomaly consensus must form with quorum")
    if result["activation_allowed"] is not False:
        raise RuntimeError("global anomaly consensus must not activate")


def main() -> int:
    try:
        validate()
        print("Afriprog global anomaly consensus validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog global anomaly consensus validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
