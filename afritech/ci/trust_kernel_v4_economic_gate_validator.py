from __future__ import annotations

from afritech.trust_kernel.economic_gate import (
    TRUST_KERNEL_V4_STATUS,
    EconomicActivationBlocked,
    EconomicEvidenceSignals,
    evaluate_economic_activation,
    guard_economic_activation,
)


def validate() -> bool:
    decision = evaluate_economic_activation()
    if decision.authorized:
        raise SystemExit("Trust Kernel v4 economic layer activated without evidence")
    if decision.status != TRUST_KERNEL_V4_STATUS:
        raise SystemExit(f"unexpected Trust Kernel v4 status: {decision.status}")

    try:
        guard_economic_activation(EconomicEvidenceSignals())
    except EconomicActivationBlocked:
        return True

    raise SystemExit("economic activation guard did not block missing evidence")


def main() -> int:
    validate()
    print("TRUST_KERNEL_V4_ECONOMIC_GATE_VALIDATOR: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
