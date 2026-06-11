from __future__ import annotations

import sys

from afritech.extensions.afriprog.copilot_assist.federation_governance import (
    build_federation_message,
    verify_federation_message,
)

VALIDATOR_NAME = "afritech.ci.afriprog_cross_network_signature_validator"


def validate() -> None:
    message = build_federation_message(
        network_id="network-A",
        proposal_id="PROP-GLOBAL-1",
        vote="yes",
    )
    if verify_federation_message(message) is not True:
        raise RuntimeError("valid federation signature rejected")
    tampered = type(message)(
        **{**message.canonical_dict(), "signature": "bad", "schema": message.schema}
    )
    if verify_federation_message(tampered):
        raise RuntimeError("invalid federation signature accepted")


def main() -> int:
    try:
        validate()
        print("Afriprog cross-network signature validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog cross-network signature validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
