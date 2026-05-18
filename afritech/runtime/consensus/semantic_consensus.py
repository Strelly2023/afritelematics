from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticConsensusResult:
    agreed: bool
    hash: str | None
    participants: int


def local_consensus(hashes: list[str]) -> SemanticConsensusResult:
    if not hashes:
        return SemanticConsensusResult(agreed=False, hash=None, participants=0)
    first = hashes[0]
    return SemanticConsensusResult(
        agreed=all(value == first for value in hashes),
        hash=first,
        participants=len(hashes),
    )
