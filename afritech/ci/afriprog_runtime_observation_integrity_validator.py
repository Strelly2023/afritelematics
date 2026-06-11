from __future__ import annotations

import sys

from afritech.runtime_verification import observe_runtime
from afritech.runtime_verification.verification_validators import (
    validate_observation_integrity,
)


def validate() -> None:
    observation = observe_runtime(
        event="OrderShipped",
        state_before="Pending",
        expected_state="Paid",
        observed_state="Pending",
        contract="order_must_be_paid_before_shipping",
    )
    result = validate_observation_integrity(observation)
    if result["valid"] is not True:
        raise RuntimeError(f"valid observation rejected: {result}")

    invalid = dict(observation)
    invalid["runtime_mutation_allowed"] = True
    invalid_result = validate_observation_integrity(invalid)
    if invalid_result["valid"] is not False:
        raise RuntimeError("mutating observation was admitted")


def main() -> int:
    try:
        validate()
        print("Afriprog runtime observation integrity validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog runtime observation integrity validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
