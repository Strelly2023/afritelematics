from __future__ import annotations

import sys

from afritech.runtime_verification import detect_drift, evaluate_contracts, observe_runtime


def validate() -> None:
    observation = observe_runtime(
        event="OrderShipped",
        state_before="Pending",
        expected_state="Paid",
        observed_state="Pending",
        contract="order_must_be_paid_before_shipping",
    )
    evaluation = evaluate_contracts(observation)
    drift = detect_drift(observation, evaluation)
    if drift is None:
        raise RuntimeError("contract drift was not detected")
    if drift["type"] != "state_violation":
        raise RuntimeError(f"unexpected drift type: {drift}")


def main() -> int:
    try:
        validate()
        print("Afriprog drift detection validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog drift detection validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
