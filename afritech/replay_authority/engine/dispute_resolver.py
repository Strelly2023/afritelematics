"""Resolve claims against replay-derived authority."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from afritech.replay_authority.engine.reconstruct import (
    ReplayAuthorityReconstruction,
    decision_index,
    reconstruct_authority,
)


@dataclass(frozen=True)
class DisputeClaim:
    claim_id: str
    claimant_id: str
    decision_id: str
    asserted_value: object
    supporting_event_ids: tuple[str, ...] = ()

    def canonical_dict(self) -> dict[str, object]:
        return {
            "asserted_value": self.asserted_value,
            "claim_id": self.claim_id,
            "claimant_id": self.claimant_id,
            "decision_id": self.decision_id,
            "supporting_event_ids": list(self.supporting_event_ids),
        }


@dataclass(frozen=True)
class ClaimResolution:
    claim: DisputeClaim
    admitted: bool
    reason: str
    authoritative_value: object | None
    authority_hash: str | None

    def canonical_dict(self) -> dict[str, object]:
        return {
            "admitted": self.admitted,
            "authoritative_value": self.authoritative_value,
            "authority_hash": self.authority_hash,
            "claim": self.claim.canonical_dict(),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class DisputeResolution:
    reconstruction: ReplayAuthorityReconstruction
    claims: tuple[DisputeClaim, ...]
    resolutions: tuple[ClaimResolution, ...]

    @property
    def claims_hash(self) -> str:
        return _canonical_hash([claim.canonical_dict() for claim in self.claims])

    @property
    def resolution_hash(self) -> str:
        return _canonical_hash(
            [resolution.canonical_dict() for resolution in self.resolutions]
        )

    @property
    def verified(self) -> bool:
        return all(
            resolution.authority_hash is not None
            for resolution in self.resolutions
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "claims": [claim.canonical_dict() for claim in self.claims],
            "claims_hash": self.claims_hash,
            "reconstruction": self.reconstruction.canonical_dict(),
            "resolution_hash": self.resolution_hash,
            "resolutions": [
                resolution.canonical_dict() for resolution in self.resolutions
            ],
            "verified": self.verified,
        }


def resolve_dispute(
    trace: Iterable[Mapping[str, Any]],
    claims: Iterable[DisputeClaim],
) -> DisputeResolution:
    reconstruction = reconstruct_authority(trace)
    ordered_claims = tuple(sorted(claims, key=lambda item: item.claim_id))
    index = decision_index(reconstruction)
    resolutions = tuple(_resolve_claim(index, claim) for claim in ordered_claims)
    return DisputeResolution(
        claims=ordered_claims,
        reconstruction=reconstruction,
        resolutions=resolutions,
    )


def _resolve_claim(
    decisions,
    claim: DisputeClaim,
) -> ClaimResolution:
    decision = decisions.get(claim.decision_id)
    if decision is None:
        return ClaimResolution(
            admitted=False,
            authoritative_value=None,
            authority_hash=None,
            claim=claim,
            reason="decision_not_reconstructable",
        )
    supported = set(claim.supporting_event_ids) <= set(decision.evidence_event_ids)
    if not supported:
        return ClaimResolution(
            admitted=False,
            authoritative_value=decision.authoritative_value,
            authority_hash=decision.authority_hash,
            claim=claim,
            reason="supporting_events_not_authoritative",
        )
    if claim.asserted_value != decision.authoritative_value:
        return ClaimResolution(
            admitted=False,
            authoritative_value=decision.authoritative_value,
            authority_hash=decision.authority_hash,
            claim=claim,
            reason="claim_conflicts_with_replay_authority",
        )
    return ClaimResolution(
        admitted=True,
        authoritative_value=decision.authoritative_value,
        authority_hash=decision.authority_hash,
        claim=claim,
        reason="claim_matches_replay_authority",
    )


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

