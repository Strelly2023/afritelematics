from __future__ import annotations

import sys

from afritech.extensions.afriprog.copilot_assist import validate_context_proposal
from afritech.runtime_monitoring import (
    anomaly_to_proposal,
    build_anomaly_context,
    classify_anomaly,
)

VALIDATOR_NAME = "afritech.ci.afriprog_anomaly_proposal_conversion_validator"


def validate() -> None:
    anomaly = classify_anomaly({"type": "contract_mismatch"})
    context = build_anomaly_context(
        anomaly,
        timestamp="2026-06-06T00:00:00Z",
        affected_files=("afritech/api/driver.py",),
    )
    proposal = anomaly_to_proposal(anomaly, context)
    validation = validate_context_proposal(proposal)
    if validation["status"] != "ready_for_governance":
        raise RuntimeError("anomaly proposal must be governance-ready")
    if proposal.activation_allowed is not False:
        raise RuntimeError("anomaly proposal must not activate")


def main() -> int:
    try:
        validate()
        print("Afriprog anomaly proposal conversion validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog anomaly proposal conversion validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
