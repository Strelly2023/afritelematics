from __future__ import annotations

import sys

from afritech.extensions.afriprog.copilot_assist.federation_governance import (
    validate_constitutional_compliance,
)

VALIDATOR_NAME = "afritech.ci.afriprog_constitutional_compliance_validator"


def validate() -> None:
    compliant = validate_constitutional_compliance(
        {
            "replay_required": True,
            "validators_required": True,
            "governance_required": True,
            "local_activation_sovereignty": True,
            "runtime_mutation_protected": True,
        }
    )
    violating = validate_constitutional_compliance({"replay_required": True})
    if compliant["compliant"] is not True:
        raise RuntimeError("compliant federation proposal rejected")
    if violating["compliant"] is not False:
        raise RuntimeError("violating federation proposal accepted")


def main() -> int:
    try:
        validate()
        print("Afriprog constitutional compliance validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog constitutional compliance validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
