from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Dict, Iterable, Mapping

from afritech.distributed.consensus.validator import ProofValidator as DistributedProofValidator


class PBFTConsensusError(RuntimeError):
    """Raised when PBFT-style consensus fails."""


@dataclass(frozen=True)
class PBFTConsensusCertificate:
    height: int
    round: int
    validator_count: int
    fault_tolerance: int
    quorum: int
    proposal_hash: str
    leader_node_id: str
    pre_prepare_nodes: tuple[str, ...]
    prepare_nodes: tuple[str, ...]
    commit_nodes: tuple[str, ...]
    proof_hash: str
    authority_boundary: str = "pbft_tendermint_consensus_only"

    @property
    def verified(self) -> bool:
        return (
            self.validator_count >= 1
            and self.fault_tolerance >= 0
            and self.quorum == (2 * self.fault_tolerance) + 1
            and len(self.proposal_hash) == 64
            and len(self.proof_hash) == 64
            and len(self.pre_prepare_nodes) >= 1
            and len(self.prepare_nodes) >= self.quorum
            and len(self.commit_nodes) >= self.quorum
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_boundary": self.authority_boundary,
            "commit_nodes": list(self.commit_nodes),
            "fault_tolerance": self.fault_tolerance,
            "height": self.height,
            "leader_node_id": self.leader_node_id,
            "pre_prepare_nodes": list(self.pre_prepare_nodes),
            "prepare_nodes": list(self.prepare_nodes),
            "proposal_hash": self.proposal_hash,
            "quorum": self.quorum,
            "round": self.round,
            "schema": "afritech.distributed.pbft_consensus_certificate.v1",
            "validator_count": self.validator_count,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


class PBFTConsensusEngine:
    """
    PBFT / Tendermint-style consensus over proof-carrying execution results.

    The engine requires:
    - one pre-prepare proposal
    - >= 2f + 1 prepares
    - >= 2f + 1 commits
    where f = floor((n - 1) / 3)
    """

    def __init__(
        self,
        *,
        validator_count: int | None = None,
        height: int = 1,
        round: int = 0,
        require_pre_prepare: bool = True,
        validator: DistributedProofValidator | None = None,
    ) -> None:
        self.validator_count = validator_count
        self.height = height
        self.round = round
        self.require_pre_prepare = require_pre_prepare
        self.validator = validator or DistributedProofValidator()

    def decide(self, proofs: Iterable[Dict[str, Any]], total_nodes: int | None = None) -> PBFTConsensusCertificate:
        proof_list = list(proofs)
        if not proof_list:
            raise PBFTConsensusError("no_proofs_supplied")

        validator_count = total_nodes or self.validator_count or len({str(proof.get("node")) for proof in proof_list})
        if not isinstance(validator_count, int) or validator_count <= 0:
            raise PBFTConsensusError("invalid_validator_count")

        fault_tolerance = max(0, (validator_count - 1) // 3)
        quorum = (2 * fault_tolerance) + 1

        grouped: dict[str, dict[str, set[str] | list[dict[str, Any]]]] = defaultdict(
            lambda: {
                "pre_prepare": set(),
                "prepare": set(),
                "commit": set(),
                "proofs": [],
            }
        )

        for proof in proof_list:
            if not self.validator.validate(proof):
                raise PBFTConsensusError("invalid_proof")

            node_id = str(proof.get("node") or "")
            result_hash = str(proof.get("hash") or "")
            stage = _stage_from_proof(proof)

            if not node_id or not result_hash:
                raise PBFTConsensusError("invalid_consensus_vote")
            if stage not in {"pre_prepare", "prepare", "commit"}:
                raise PBFTConsensusError(f"invalid_consensus_stage: {stage}")

            grouped[result_hash][stage].add(node_id)
            grouped[result_hash]["proofs"].append(proof)

        winners: list[tuple[str, dict[str, set[str] | list[dict[str, Any]]]]] = []
        for result_hash, state in grouped.items():
            pre_prepare_nodes = state["pre_prepare"]
            prepare_nodes = state["prepare"]
            commit_nodes = state["commit"]
            if self.require_pre_prepare and len(pre_prepare_nodes) < 1:
                continue
            if len(prepare_nodes) < quorum or len(commit_nodes) < quorum:
                continue
            winners.append((result_hash, state))

        if not winners:
            raise PBFTConsensusError(
                "pbft_finality_not_reached"
            )

        def _rank(item: tuple[str, dict[str, set[str] | list[dict[str, Any]]]]) -> tuple[int, int, str]:
            result_hash, state = item
            commit_nodes = state["commit"]
            prepare_nodes = state["prepare"]
            return (-len(commit_nodes), -len(prepare_nodes), result_hash)

        proposal_hash, state = sorted(winners, key=_rank)[0]
        pre_prepare_nodes = tuple(sorted(state["pre_prepare"]))
        prepare_nodes = tuple(sorted(state["prepare"]))
        commit_nodes = tuple(sorted(state["commit"]))
        leader_node_id = pre_prepare_nodes[0] if pre_prepare_nodes else prepare_nodes[0]

        certificate = PBFTConsensusCertificate(
            height=self.height,
            round=self.round,
            validator_count=validator_count,
            fault_tolerance=fault_tolerance,
            quorum=quorum,
            proposal_hash=proposal_hash,
            leader_node_id=leader_node_id,
            pre_prepare_nodes=pre_prepare_nodes,
            prepare_nodes=prepare_nodes,
            commit_nodes=commit_nodes,
            proof_hash=_canonical_hash(
                {
                    "height": self.height,
                    "proposal_hash": proposal_hash,
                    "quorum": quorum,
                    "round": self.round,
                    "validator_count": validator_count,
                    "votes": {
                        "commit": list(commit_nodes),
                        "pre_prepare": list(pre_prepare_nodes),
                        "prepare": list(prepare_nodes),
                    },
                }
            ),
        )

        if not certificate.verified:
            raise PBFTConsensusError("pbft_certificate_construction_failed")

        return certificate

    def __repr__(self) -> str:
        return (
            f"<PBFTConsensusEngine validators={self.validator_count} "
            f"height={self.height} round={self.round} require_pre_prepare={self.require_pre_prepare}>"
        )


def _stage_from_proof(proof: Mapping[str, Any]) -> str:
    metadata = proof.get("metadata")
    if isinstance(metadata, Mapping):
        for key in ("protocol_step", "pbft_step", "consensus_step", "stage"):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip().lower()
    return "commit"


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()
