from __future__ import annotations

import sys

from afritech.runtime_verification import classify_drift, coordinate_agents, detect_drift, evaluate_contracts, observe_runtime


def validate() -> None:
    observation = observe_runtime(
        event="OrderShipped",
        state_before="Pending",
        expected_state="Paid",
        observed_state="Pending",
        contract="order_must_be_paid_before_shipping",
    )
    drift = classify_drift(detect_drift(observation, evaluate_contracts(observation)) or {})
    coordinated = coordinate_agents((drift,))
    for payload in (observation, drift, coordinated):
        for key in ("activation_allowed", "runtime_mutation_allowed", "rollback_execution_allowed"):
            if payload[key] is not False:
                raise RuntimeError(f"verification agent gained authority: {key}")


def main() -> int:
    try:
        validate()
        print("Afriprog agent non-authority validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog agent non-authority validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
