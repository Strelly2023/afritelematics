"""Replay-native evidence index for feature-registry projection."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Literal

from afritech.features import (
    EvidenceKind,
    EvidenceRef,
    FeatureEvidence,
    file_sha256,
    ROOT,
)


EvidenceType = Literal["replay", "proof", "test", "implementation", "boundary_guard"]


@dataclass(frozen=True)
class EvidenceEvent:
    id: str
    timestamp: str
    evidence_refs: tuple[EvidenceRef, ...]

    def canonical_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceArtifact:
    id: str
    type: EvidenceType
    path: str
    hash: str
    origin_event: str
    timestamp: str
    required: bool

    def canonical_dict(self) -> dict[str, object]:
        return asdict(self)


def replay_events_from_feature_candidates(
    candidates: Iterable[FeatureEvidence],
) -> tuple[EvidenceEvent, ...]:
    return tuple(
        EvidenceEvent(
            id=f"feature-evidence:{candidate.id}:{candidate.version}",
            timestamp=f"{candidate.last_updated}T00:00:00Z",
            evidence_refs=candidate.evidence,
        )
        for candidate in candidates
    )


def build_evidence_index(
    event_store: Iterable[EvidenceEvent],
) -> dict[str, EvidenceArtifact]:
    artifacts: dict[str, EvidenceArtifact] = {}

    for event in event_store:
        for evidence in event.evidence_refs:
            path = ROOT / evidence.path
            if not path.exists() or not path.is_file():
                continue
            artifacts[evidence.path] = EvidenceArtifact(
                id=f"{event.id}:{evidence.path}",
                type=_evidence_type(evidence.kind),
                path=evidence.path,
                hash=file_sha256(path),
                origin_event=event.id,
                timestamp=event.timestamp,
                required=evidence.required,
            )

    return artifacts


def _evidence_type(kind: EvidenceKind) -> EvidenceType:
    return kind
