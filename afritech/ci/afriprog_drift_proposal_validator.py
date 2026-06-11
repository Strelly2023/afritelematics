from __future__ import annotations

import sys

from afritech.runtime_verification import (
    build_drift_context,
    classify_drift,
    detect_drift,
    drift_to_proposal,
    evaluate_contracts,
    observe_runtime,
)


def validate() -> None:
    observation = observe_runtime(
        event="OrderShipped",
        state_before="Pending",
        expected_state="Paid",
        observed_state="Pending",
        contract="order_must_be_paid_before_shipping",
        trace=("OrderCreated", "OrderShipped"),
    )
    drift = detect_drift(observation, evaluate_contracts(observation))
    classified = classify_drift(drift or {})
    context = build_drift_context(
        classified,
        timestamp="2026-06-06T00:00:00Z",
        affected_files=("contracts/order.yaml",),
    )
    proposal = drift_to_proposal(classified, context).canonical_dict()
    if proposal["governance_required"] is not True:
        raise RuntimeError("drift proposal must require governance")
    if proposal["replay_required"] is not True:
        raise RuntimeError("drift proposal must require replay")
    if proposal["rollback_required"] is not True:
        raise RuntimeError("drift proposal must require rollback readiness")
    if proposal["activation_allowed"] is not False:
        raise RuntimeError("drift proposal must not activate")
    if proposal["runtime_mutation_allowed"] is not False:
        raise RuntimeError("drift proposal must not mutate runtime")


def main() -> int:
    try:
        validate()
        print("Afriprog drift proposal validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog drift proposal validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
