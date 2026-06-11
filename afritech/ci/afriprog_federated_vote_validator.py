from __future__ import annotations

import sys

from afritech.extensions.afriprog.copilot_assist.federation_governance import (
    build_federation_message,
    compute_federated_vote,
)

VALIDATOR_NAME = "afritech.ci.afriprog_federated_vote_validator"


def validate() -> None:
    messages = (
        build_federation_message(network_id="network-A", proposal_id="P", vote="yes"),
        build_federation_message(network_id="network-B", proposal_id="P", vote="yes"),
        build_federation_message(network_id="network-C", proposal_id="P", vote="no"),
    )
    result = compute_federated_vote(messages, quorum_ratio=0.66)
    if result["consensus_reached"] is not True:
        raise RuntimeError("federated vote should reach consensus")
    if result["governance_outcome"] != "LOCAL_APPROVAL_REQUIRED":
        raise RuntimeError("federated vote must require local approval")


def main() -> int:
    try:
        validate()
        print("Afriprog federated vote validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog federated vote validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
