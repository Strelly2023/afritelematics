from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Final


FEDERATION_SCHEMA: Final[str] = "afri-fed.constitutional_governance.v2"
GLOBAL_INVARIANTS: Final[tuple[str, ...]] = (
    "replay_required",
    "validators_required",
    "governance_required",
    "local_activation_sovereignty",
    "runtime_mutation_protected",
)


@dataclass(frozen=True)
class FederationMessage:
    network_id: str
    proposal_id: str
    constitution_version: str
    vote: str
    confidence: float
    signature: str
    schema: str = FEDERATION_SCHEMA
    external_activation_allowed: bool = False
    external_runtime_mutation_allowed: bool = False
    local_sovereignty_preserved: bool = True

    def canonical_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "network_id": self.network_id,
            "proposal_id": self.proposal_id,
            "constitution_version": self.constitution_version,
            "vote": self.vote,
            "confidence": self.confidence,
            "signature": self.signature,
            "external_activation_allowed": self.external_activation_allowed,
            "external_runtime_mutation_allowed": self.external_runtime_mutation_allowed,
            "local_sovereignty_preserved": self.local_sovereignty_preserved,
        }


def sign_federation_vote(
    *,
    network_id: str,
    proposal_id: str,
    vote: str,
) -> str:
    return hashlib.sha256(f"{network_id}:{proposal_id}:{vote}".encode()).hexdigest()


def build_federation_message(
    *,
    network_id: str,
    proposal_id: str,
    vote: str,
    constitution_version: str = "v2.0",
    confidence: float = 0.9,
) -> FederationMessage:
    return FederationMessage(
        network_id=network_id,
        proposal_id=proposal_id,
        constitution_version=constitution_version,
        vote=vote,
        confidence=confidence,
        signature=sign_federation_vote(
            network_id=network_id,
            proposal_id=proposal_id,
            vote=vote,
        ),
    )


def verify_federation_message(message: FederationMessage) -> bool:
    expected = sign_federation_vote(
        network_id=message.network_id,
        proposal_id=message.proposal_id,
        vote=message.vote,
    )
    return (
        message.signature == expected
        and message.external_activation_allowed is False
        and message.external_runtime_mutation_allowed is False
        and message.local_sovereignty_preserved is True
    )


def compute_federated_vote(
    messages: tuple[FederationMessage, ...],
    *,
    quorum_ratio: float = 0.66,
) -> dict[str, object]:
    verified = tuple(message for message in messages if verify_federation_message(message))
    yes_votes = tuple(message for message in verified if message.vote == "yes")
    ratio = len(yes_votes) / len(verified) if verified else 0.0
    return {
        "verified_networks": len(verified),
        "yes_votes": len(yes_votes),
        "consensus_reached": ratio >= quorum_ratio,
        "governance_outcome": "LOCAL_APPROVAL_REQUIRED",
        "external_activation_allowed": False,
        "external_runtime_mutation_allowed": False,
        "local_sovereignty_preserved": True,
    }


def validate_constitutional_compliance(proposal: dict[str, object]) -> dict[str, object]:
    missing = tuple(
        invariant
        for invariant in GLOBAL_INVARIANTS
        if proposal.get(invariant) is not True
    )
    return {
        "compliant": not missing,
        "missing_invariants": missing,
        "external_activation_allowed": False,
        "local_sovereignty_preserved": True,
    }


def federation_status() -> dict[str, object]:
    payload = {
        "schema": FEDERATION_SCHEMA,
        "global_invariants": GLOBAL_INVARIANTS,
        "federation": "enabled_as_governance_coordination",
        "cross_network_governance": "non_authoritative",
        "local_sovereignty": "preserved",
        "activation_authority": "local_only",
        "runtime_mutation": "protected",
    }
    payload["status_hash"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return payload


__all__ = [
    "FEDERATION_SCHEMA",
    "GLOBAL_INVARIANTS",
    "FederationMessage",
    "build_federation_message",
    "compute_federated_vote",
    "federation_status",
    "sign_federation_vote",
    "validate_constitutional_compliance",
    "verify_federation_message",
]
