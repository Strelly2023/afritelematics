from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from afritech.distributed.consensus.aggregator import ProofAggregator
from afritech.distributed.consensus.errors import ProofValidationError, QuorumNotReached
from afritech.distributed.consensus.quorum import QuorumPolicy
from afritech.distributed.consensus.validator import ProofValidator
from afritech.distributed.consensus.voting import Vote, vote_from_proof


@dataclass(frozen=True)
class ConsensusResult:
    result: Any
    result_hash: str
    votes: int
    total_nodes: int
    quorum: int
    node_ids: List[str]
    proofs: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result": self.result,
            "result_hash": self.result_hash,
            "votes": self.votes,
            "total_nodes": self.total_nodes,
            "quorum": self.quorum,
            "node_ids": list(self.node_ids),
            "proofs": list(self.proofs),
        }


class ProofConsensusEngine:
    """
    GA-Elite proof consensus orchestrator.
    """

    def __init__(
        self,
        quorum_policy: Optional[QuorumPolicy] = None,
        validator: Optional[ProofValidator] = None,
        aggregator: Optional[ProofAggregator] = None,
    ) -> None:
        self.quorum_policy = quorum_policy or QuorumPolicy()
        self.validator = validator or ProofValidator()
        self.aggregator = aggregator or ProofAggregator()

    def decide(
        self,
        proofs: Iterable[Dict[str, Any]],
        total_nodes: Optional[int] = None,
    ) -> ConsensusResult:
        proof_list = list(proofs)
        if not proof_list:
            raise ProofValidationError("no proofs supplied")

        total = total_nodes if total_nodes is not None else len(proof_list)
        quorum = self.quorum_policy.required_votes(total)

        votes: List[Vote] = []
        for proof in proof_list:
            accepted = self.validator.validate(proof)
            votes.append(
                vote_from_proof(
                    proof,
                    accepted,
                    "" if accepted else "invalid_proof",
                )
            )

        grouped = self.aggregator.aggregate(votes)
        winner = self.aggregator.winner(grouped)

        if not self.quorum_policy.has_quorum(winner.votes, total):
            raise QuorumNotReached(
                f"winner has {winner.votes} votes; quorum requires {quorum}"
            )

        result = winner.proofs[0]["result"]
        return ConsensusResult(
            result=result,
            result_hash=winner.result_hash,
            votes=winner.votes,
            total_nodes=total,
            quorum=quorum,
            node_ids=list(winner.node_ids),
            proofs=list(winner.proofs),
        )

    def finalize(
        self,
        proofs: Iterable[Dict[str, Any]],
        total_nodes: Optional[int] = None,
    ) -> tuple[Any | None, List[Dict[str, Any]]]:
        try:
            result = self.decide(proofs, total_nodes=total_nodes)
        except Exception:
            return None, []

        return result.result, list(result.proofs)
