"""Replay-derived authority reconstruction."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from afritech.runtime.entropy.convergence import ConvergenceResult, converge


@dataclass(frozen=True)
class AuthorityDecision:
    decision_id: str
    decision_type: str
    subject_id: str
    authoritative_value: object
    evidence_event_ids: tuple[str, ...]
    replay_hash: str

    @property
    def authority_hash(self) -> str:
        return _canonical_hash(
            {
                "authoritative_value": self.authoritative_value,
                "decision_id": self.decision_id,
                "decision_type": self.decision_type,
                "evidence_event_ids": list(self.evidence_event_ids),
                "replay_hash": self.replay_hash,
                "subject_id": self.subject_id,
            }
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authoritative_value": self.authoritative_value,
            "authority_hash": self.authority_hash,
            "decision_id": self.decision_id,
            "decision_type": self.decision_type,
            "evidence_event_ids": list(self.evidence_event_ids),
            "replay_hash": self.replay_hash,
            "subject_id": self.subject_id,
        }


@dataclass(frozen=True)
class ReplayAuthorityReconstruction:
    convergence: ConvergenceResult
    decisions: tuple[AuthorityDecision, ...]

    @property
    def decisions_hash(self) -> str:
        return _canonical_hash([decision.canonical_dict() for decision in self.decisions])

    @property
    def replay_authority_hash(self) -> str:
        return _canonical_hash(
            {
                "decisions_hash": self.decisions_hash,
                "replay_hash": self.convergence.replay_hash,
            }
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "convergence": self.convergence.canonical_dict(),
            "decisions": [decision.canonical_dict() for decision in self.decisions],
            "decisions_hash": self.decisions_hash,
            "replay_authority_hash": self.replay_authority_hash,
        }


def reconstruct_authority(
    trace: Iterable[Mapping[str, Any]],
) -> ReplayAuthorityReconstruction:
    convergence = converge(trace)
    events = tuple(convergence.accepted_events)
    ride_ids = sorted(
        {
            str(event.payload.get("ride_id"))
            for event in events
            if event.payload.get("ride_id")
        }
    )
    decisions: list[AuthorityDecision] = []
    for ride_id in ride_ids:
        ride_events = tuple(
            event for event in events if event.payload.get("ride_id") == ride_id
        )
        decisions.extend(_decisions_for_ride(ride_id, ride_events, convergence.replay_hash))
    return ReplayAuthorityReconstruction(
        convergence=convergence,
        decisions=tuple(
            sorted(decisions, key=lambda item: (item.subject_id, item.decision_id))
        ),
    )


def decision_index(
    reconstruction: ReplayAuthorityReconstruction,
) -> dict[str, AuthorityDecision]:
    return {decision.decision_id: decision for decision in reconstruction.decisions}


def _decisions_for_ride(
    ride_id: str,
    events,
    replay_hash: str,
) -> tuple[AuthorityDecision, ...]:
    by_action = {str(event.payload.get("action")): event for event in events}
    decisions: list[AuthorityDecision] = []
    status = "completed" if "complete" in by_action else "incomplete"
    decisions.append(
        AuthorityDecision(
            authoritative_value=status,
            decision_id=f"{ride_id}:ride_status",
            decision_type="ride_status",
            evidence_event_ids=tuple(event.event_id for event in events),
            replay_hash=replay_hash,
            subject_id=ride_id,
        )
    )
    if "price_quote" in by_action:
        quote = by_action["price_quote"]
        decisions.append(
            AuthorityDecision(
                authoritative_value=int(quote.payload.get("fare_cents", 0)),
                decision_id=f"{ride_id}:fare_cents",
                decision_type="fare_cents",
                evidence_event_ids=(quote.event_id,),
                replay_hash=replay_hash,
                subject_id=ride_id,
            )
        )
    if "match" in by_action:
        match = by_action["match"]
        decisions.append(
            AuthorityDecision(
                authoritative_value=str(match.payload.get("driver_id", "unknown")),
                decision_id=f"{ride_id}:matched_driver",
                decision_type="matched_driver",
                evidence_event_ids=(match.event_id,),
                replay_hash=replay_hash,
                subject_id=ride_id,
            )
        )
    return tuple(decisions)


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

