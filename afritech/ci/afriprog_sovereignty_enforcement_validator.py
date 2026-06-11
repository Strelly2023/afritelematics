from __future__ import annotations

import sys

from afritech.extensions.afriprog.copilot_assist.federation_governance import (
    build_federation_message,
    compute_federated_vote,
)

VALIDATOR_NAME = "afritech.ci.afriprog_sovereignty_enforcement_validator"


def validate() -> None:
    messages = (
        build_federation_message(network_id="network-A", proposal_id="P", vote="yes"),
        build_federation_message(network_id="network-B", proposal_id="P", vote="yes"),
    )
    result = compute_federated_vote(messages)
    if result["local_sovereignty_preserved"] is not True:
        raise RuntimeError("federation must preserve local sovereignty")
    if result["external_activation_allowed"] is not False:
        raise RuntimeError("external activation must be denied")
    if result["external_runtime_mutation_allowed"] is not False:
        raise RuntimeError("external runtime mutation must be denied")


def main() -> int:
    try:
        validate()
        print("Afriprog sovereignty enforcement validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog sovereignty enforcement validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
