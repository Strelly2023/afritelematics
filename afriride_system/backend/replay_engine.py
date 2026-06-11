"""Deterministic replay from persisted trace lineage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afriride_system.backend.authority_runtime import DOC_VERSION, authority_envelope
from afriride_system.backend.trace_enforcement import (
    TraceEvent,
    recompute_trace_event_hash,
    stable_hash,
    trace_hash_for,
)

__doc_authority__ = "DOC-ARCH-001"
__doc_version__ = "1.0.0"
__governed_invariants__ = (
    "I3_NO_SILENT_MUTATION",
    "I4_DETERMINISTIC_EXECUTION",
    "I5_REPLAY_REQUIRED",
    "I6_REPLAY_AUTHORITY",
    "I7_TRANSCRIPT_COMPLETENESS",
    "I8_TRANSCRIPT_HASH_STABILITY",
    "I11_AUTHORITY_DECLARATION",
)


ALLOWED_TRANSITIONS: dict[str | None, frozenset[str]] = {
    None: frozenset({"REQUESTED"}),
    "REQUESTED": frozenset({"DRIVER_ACCEPTED", "REJECTED", "CANCELLED"}),
    "DRIVER_ACCEPTED": frozenset({"ARRIVED", "CANCELLED"}),
    "ARRIVED": frozenset({"STARTED", "CANCELLED"}),
    "STARTED": frozenset({"COMPLETED", "CANCELLED"}),
    "COMPLETED": frozenset(),
    "CANCELLED": frozenset(),
    "REJECTED": frozenset(),
}


@dataclass(frozen=True)
class ReplaySnapshot:
    ride_id: str
    status: str
    assigned_driver: str | None
    passenger_id: str | None
    transitions: tuple[str, ...]
    trace_hash: str
    replay_hash: str
    replay_verified: bool
    ordered: bool
    hash_chain_verified: bool
    invariant_violations: tuple[str, ...]
    terminal_event_hash: str | None

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "ride_id": self.ride_id,
            "status": self.status,
            "assigned_driver": self.assigned_driver,
            "passenger_id": self.passenger_id,
            "transitions": list(self.transitions),
            "trace_hash": self.trace_hash,
            "replay_hash": self.replay_hash,
            "replay_verified": self.replay_verified,
            "ordered": self.ordered,
            "hash_chain_verified": self.hash_chain_verified,
            "invariant_violations": list(self.invariant_violations),
            "terminal_event_hash": self.terminal_event_hash,
            "authority": authority_envelope(
                doc_id=__doc_authority__,
                doc_version=__doc_version__,
                governed_invariants=__governed_invariants__,
                surface="replay_snapshot",
            ),
        }


class ReplayEngine:
    """Reconstruct ride state from persisted trace events only."""

    def replay(self, ride_id: str, events: tuple[TraceEvent, ...]) -> ReplaySnapshot:
        authority = authority_envelope(
            doc_id=__doc_authority__,
            doc_version=__doc_version__,
            governed_invariants=__governed_invariants__,
            surface="replay_snapshot",
        )
        ordered = all(left.sequence_id < right.sequence_id for left, right in zip(events, events[1:]))
        status = "UNKNOWN"
        assigned_driver: str | None = None
        passenger_id: str | None = None
        transitions: list[str] = []
        invariant_violations: list[str] = []
        seen_transitions: set[str] = set()
        previous_transition: str | None = None
        hash_chain_verified = True

        if not ordered and events:
            invariant_violations.append("sequence_order_break")

        for event in events:
            if event.event_hash != recompute_trace_event_hash(event):
                hash_chain_verified = False
                invariant_violations.append(f"event_hash_mismatch:{event.event_id}")
            transition = event.transition
            if transition is None:
                continue
            allowed_next = ALLOWED_TRANSITIONS.get(previous_transition, frozenset())
            if transition in seen_transitions:
                invariant_violations.append(f"duplicate_transition:{transition}")
            elif transition not in allowed_next:
                source = previous_transition or "INITIAL"
                invariant_violations.append(f"invalid_transition:{source}->{transition}")
            else:
                previous_transition = transition
            transitions.append(transition)
            seen_transitions.add(transition)
            if transition == "REQUESTED":
                status = "REQUESTED"
                if event.actor_type == "rider":
                    passenger_id = event.actor_id
            elif transition == "DRIVER_ACCEPTED":
                status = "DRIVER_ASSIGNED"
                if event.actor_type == "driver":
                    assigned_driver = event.actor_id
            elif transition == "ARRIVED":
                status = "DRIVER_ARRIVED"
                if event.actor_type == "driver":
                    assigned_driver = event.actor_id
            elif transition == "STARTED":
                status = "IN_TRIP"
                if event.actor_type == "driver":
                    assigned_driver = event.actor_id
            elif transition == "COMPLETED":
                status = "COMPLETED"
                if event.actor_type == "driver":
                    assigned_driver = event.actor_id
            elif transition == "CANCELLED":
                status = "CANCELED"
            elif transition == "REJECTED":
                status = "REJECTED"

        trace_hash = trace_hash_for(events)
        replay_hash = stable_hash(
            {
                "ride_id": ride_id,
                "status": status,
                "assigned_driver": assigned_driver,
                "passenger_id": passenger_id,
                "transitions": transitions,
                "ordered": ordered,
                "hash_chain_verified": hash_chain_verified,
                "invariant_violations": invariant_violations,
                "terminal_event_hash": events[-1].event_hash if events else None,
                "authority_hash": authority["authority_hash"],
            }
        )
        return ReplaySnapshot(
            ride_id=ride_id,
            status=status,
            assigned_driver=assigned_driver,
            passenger_id=passenger_id,
            transitions=tuple(transitions),
            trace_hash=trace_hash,
            replay_hash=replay_hash,
            replay_verified=ordered and hash_chain_verified and not invariant_violations,
            ordered=ordered,
            hash_chain_verified=hash_chain_verified,
            invariant_violations=tuple(invariant_violations),
            terminal_event_hash=events[-1].event_hash if events else None,
        )
