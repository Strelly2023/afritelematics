from __future__ import annotations

import sys

from afritech.runtime_verification import evaluate_contracts, observe_runtime


def validate() -> None:
    compliant = evaluate_contracts(
        observe_runtime(
            event="OrderShipped",
            state_before="Paid",
            expected_state="Paid",
            observed_state="Paid",
            contract="order_must_be_paid_before_shipping",
        )
    )
    if compliant["compliant"] is not True:
        raise RuntimeError("compliant contract observation rejected")

    noncompliant = evaluate_contracts(
        observe_runtime(
            event="OrderShipped",
            state_before="Pending",
            expected_state="Paid",
            observed_state="Pending",
            contract="order_must_be_paid_before_shipping",
        )
    )
    if noncompliant["compliant"] is not False:
        raise RuntimeError("noncompliant contract observation admitted")


def main() -> int:
    try:
        validate()
        print("Afriprog contract monitoring validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog contract monitoring validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
