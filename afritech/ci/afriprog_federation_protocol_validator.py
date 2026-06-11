from __future__ import annotations

import sys

from afritech.extensions.afriprog.copilot_assist.federation_governance import (
    build_federation_message,
    federation_status,
)

VALIDATOR_NAME = "afritech.ci.afriprog_federation_protocol_validator"


def validate() -> None:
    message = build_federation_message(
        network_id="network-A",
        proposal_id="PROP-GLOBAL-1",
        vote="yes",
    )
    status = federation_status()
    if message.schema != "afri-fed.constitutional_governance.v2":
        raise RuntimeError("federation protocol schema mismatch")
    if status["cross_network_governance"] != "non_authoritative":
        raise RuntimeError("federation governance must be non-authoritative")


def main() -> int:
    try:
        validate()
        print("Afriprog federation protocol validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog federation protocol validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
