from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from afritech.distributed.consensus.errors import ConsensusTieError
from afritech.distributed.consensus.voting import Vote


@dataclass(frozen=True)
class ProofAggregate:
    result_hash: str
    votes: int
    node_ids: List[str]
    proofs: List[dict]


class ProofAggregator:
    def aggregate(self, votes: Iterable[Vote]) -> Dict[str, ProofAggregate]:
        grouped: Dict[str, ProofAggregate] = {}
        seen_nodes: set[tuple[str, str]] = set()

        for vote in votes:
            if not vote.accepted or not vote.result_hash:
                continue

            key = (vote.node_id, vote.result_hash)
            if key in seen_nodes:
                continue
            seen_nodes.add(key)

            current = grouped.get(vote.result_hash)
            if current is None:
                grouped[vote.result_hash] = ProofAggregate(
                    result_hash=vote.result_hash,
                    votes=1,
                    node_ids=[vote.node_id],
                    proofs=[vote.proof],
                )
            else:
                grouped[vote.result_hash] = ProofAggregate(
                    result_hash=current.result_hash,
                    votes=current.votes + 1,
                    node_ids=[*current.node_ids, vote.node_id],
                    proofs=[*current.proofs, vote.proof],
                )

        return grouped

    def winner(self, grouped: Dict[str, ProofAggregate]) -> ProofAggregate:
        if not grouped:
            raise ConsensusTieError("no accepted proof groups")

        ordered = sorted(
            grouped.values(),
            key=lambda item: (-item.votes, item.result_hash),
        )

        if len(ordered) > 1 and ordered[0].votes == ordered[1].votes:
            raise ConsensusTieError("consensus tie")

        return ordered[0]
