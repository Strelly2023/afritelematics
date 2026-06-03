"""
AFRIPower Read-Only Constitutional Contract.

AFRIPower is an enterprise intelligence projection layer.

Constitutional boundary:

- consumes authority
- never creates authority
- never validates truth
- never executes runtime behavior
- never mutates receipts
- never mutates proof artifacts
- never mutates governance artifacts
- never influences replay
- never influences CI
- never influences governance

AFRIPower may:

- observe
- explain
- visualize
- project
- analyze

All AFRIPower components must satisfy this contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class AFRIPowerReadOnlyContract:
    """
    Constitutional read-only contract.
    """

    component: str
    version: str

    read_only: bool
    display_only: bool
    reference_only: bool
    projection_only: bool
    enterprise_intelligence_only: bool

    authoritative: bool

    runtime_authority: bool
    validation_authority: bool
    replay_authority: bool
    proof_authority: bool
    ci_authority: bool
    governance_authority: bool
    execution_authority: bool

    mutation_allowed: bool
    receipt_mutation_allowed: bool
    proof_mutation_allowed: bool
    governance_mutation_allowed: bool

    projection_creates_authority: bool

    law_read_only: bool
    law_non_authoritative: bool
    law_display_only: bool
    law_consumes_authority_only: bool

    law_cannot_create_authority_surface: bool

    law_cannot_influence_runtime: bool
    law_cannot_influence_replay: bool
    law_cannot_influence_proof: bool
    law_cannot_influence_ci: bool
    law_cannot_influence_governance: bool

    def canonical_dict(self) -> Dict[str, object]:
        return {
            "component": self.component,
            "version": self.version,

            "read_only": self.read_only,
            "display_only": self.display_only,
            "reference_only": self.reference_only,
            "projection_only": self.projection_only,
            "enterprise_intelligence_only":
                self.enterprise_intelligence_only,

            "authoritative": self.authoritative,

            "runtime_authority": self.runtime_authority,
            "validation_authority": self.validation_authority,
            "replay_authority": self.replay_authority,
            "proof_authority": self.proof_authority,
            "ci_authority": self.ci_authority,
            "governance_authority": self.governance_authority,
            "execution_authority": self.execution_authority,

            "mutation_allowed": self.mutation_allowed,
            "receipt_mutation_allowed":
                self.receipt_mutation_allowed,
            "proof_mutation_allowed":
                self.proof_mutation_allowed,
            "governance_mutation_allowed":
                self.governance_mutation_allowed,

            "projection_creates_authority":
                self.projection_creates_authority,

            "law_read_only":
                self.law_read_only,
            "law_non_authoritative":
                self.law_non_authoritative,
            "law_display_only":
                self.law_display_only,
            "law_consumes_authority_only":
                self.law_consumes_authority_only,

            "law_cannot_create_authority_surface":
                self.law_cannot_create_authority_surface,

            "law_cannot_influence_runtime":
                self.law_cannot_influence_runtime,

            "law_cannot_influence_replay":
                self.law_cannot_influence_replay,

            "law_cannot_influence_proof":
                self.law_cannot_influence_proof,

            "law_cannot_influence_ci":
                self.law_cannot_influence_ci,

            "law_cannot_influence_governance":
                self.law_cannot_influence_governance,
        }


AFRIPOWER_READ_ONLY_CONTRACT = AFRIPowerReadOnlyContract(
    component="AFRIPower",
    version="1.0",

    read_only=True,
    display_only=True,
    reference_only=True,
    projection_only=True,
    enterprise_intelligence_only=True,

    authoritative=False,

    runtime_authority=False,
    validation_authority=False,
    replay_authority=False,
    proof_authority=False,
    ci_authority=False,
    governance_authority=False,
    execution_authority=False,

    mutation_allowed=False,
    receipt_mutation_allowed=False,
    proof_mutation_allowed=False,
    governance_mutation_allowed=False,

    projection_creates_authority=False,

    law_read_only=True,
    law_non_authoritative=True,
    law_display_only=True,
    law_consumes_authority_only=True,

    law_cannot_create_authority_surface=True,

    law_cannot_influence_runtime=True,
    law_cannot_influence_replay=True,
    law_cannot_influence_proof=True,
    law_cannot_influence_ci=True,
    law_cannot_influence_governance=True,
)


def read_only_contract_metadata() -> Dict[str, object]:
    """
    Deterministic constitutional metadata.
    """
    return AFRIPOWER_READ_ONLY_CONTRACT.canonical_dict()


def assert_read_only_contract() -> None:
    """
    Fail closed if AFRIPower violates
    constitutional boundaries.
    """

    contract = AFRIPOWER_READ_ONLY_CONTRACT

    authority_flags = (
        contract.authoritative,
        contract.runtime_authority,
        contract.validation_authority,
        contract.replay_authority,
        contract.proof_authority,
        contract.ci_authority,
        contract.governance_authority,
        contract.execution_authority,
        contract.projection_creates_authority,
    )

    if any(authority_flags):
        raise RuntimeError(
            "AFRIPower authority boundary violation"
        )

    mutation_flags = (
        contract.mutation_allowed,
        contract.receipt_mutation_allowed,
        contract.proof_mutation_allowed,
        contract.governance_mutation_allowed,
    )

    if any(mutation_flags):
        raise RuntimeError(
            "AFRIPower mutation boundary violation"
        )

    required_flags = (
        contract.read_only,
        contract.display_only,
        contract.reference_only,
        contract.projection_only,
        contract.enterprise_intelligence_only,

        contract.law_read_only,
        contract.law_non_authoritative,
        contract.law_display_only,
        contract.law_consumes_authority_only,

        contract.law_cannot_create_authority_surface,
        contract.law_cannot_influence_runtime,
        contract.law_cannot_influence_replay,
        contract.law_cannot_influence_proof,
        contract.law_cannot_influence_ci,
        contract.law_cannot_influence_governance,
    )

    if not all(required_flags):
        raise RuntimeError(
            "AFRIPower constitutional contract violation"
        )


__all__ = [
    "AFRIPowerReadOnlyContract",
    "AFRIPOWER_READ_ONLY_CONTRACT",
    "read_only_contract_metadata",
    "assert_read_only_contract",
]
