from __future__ import annotations

from afritech.simulation.continuity.models import (
    ContinuityEvent,
    ContinuityScenarioResult,
)
from afritech.simulation.continuity.resolution import (
    canonical_identity_for,
    canonical_merge,
    continuity_hash_for,
    deterministic_coordinator,
    reject_invalid_lineage,
)


REQUIRED_METRICS = (
    "execution_admissible",
    "replay_converges",
    "identity_preserved",
    "coordination_rebuilds",
    "recovery_deterministic",
)


TARGETS = {
    "CONT-001": ("SEM-DET-001", "SEM-RPL-001", "AX-DET-002", "AX-RPL-002"),
    "CONT-002": ("SEM-RPL-001", "SEM-ADM-001", "AX-RPL-003", "AX-ADM-003"),
    "CONT-003": ("SEM-ID-001", "AX-ID-001", "AX-ID-003"),
    "CONT-004": ("SEM-DET-001", "SEM-RPL-001", "AX-DET-003", "AX-RPL-002"),
    "CONT-005": ("SEM-DET-001", "SEM-CW-001", "AX-DET-002", "AX-CW-001"),
    "CONT-006": ("SEM-ADM-001", "SEM-RPL-001", "AX-ADM-003", "AX-RPL-003"),
}


def metrics(
    *,
    execution_admissible: bool = True,
    replay_converges: bool = True,
    identity_preserved: bool = True,
    coordination_rebuilds: bool = True,
    recovery_deterministic: bool = True,
) -> dict[str, bool]:
    return {
        "execution_admissible": execution_admissible,
        "replay_converges": replay_converges,
        "identity_preserved": identity_preserved,
        "coordination_rebuilds": coordination_rebuilds,
        "recovery_deterministic": recovery_deterministic,
    }


def result(
    scenario_id: str,
    accepted: bool,
    reason: str,
    events: tuple[ContinuityEvent, ...],
    scenario_metrics: dict[str, bool],
) -> ContinuityScenarioResult:
    return ContinuityScenarioResult(
        scenario_id=scenario_id,
        accepted=accepted,
        reason=reason,
        continuity_hash=continuity_hash_for(events) if events else None,
        targets=TARGETS[scenario_id],
        metrics=scenario_metrics,
    )


def partition_survival() -> ContinuityScenarioResult:
    node_events = {
        "node-b": (
            ContinuityEvent(
                "CONT-EVT-002",
                "ride:continuity-1",
                8,
                "node-b",
                2,
                "assign_driver",
                {"driver_id": "driver:1", "status": "assigned"},
                lineage=("root",),
            ),
        ),
        "node-a": (
            ContinuityEvent(
                "CONT-EVT-001",
                "ride:continuity-1",
                8,
                "node-a",
                1,
                "request_ride",
                {"rider_id": "rider:1", "status": "requested"},
                lineage=("root",),
            ),
        ),
    }

    merged = canonical_merge(node_events)
    replay = canonical_merge(dict(reversed(tuple(node_events.items()))))
    converges = continuity_hash_for(merged) == continuity_hash_for(replay)
    ordered = [event.event_id for event in merged] == ["CONT-EVT-001", "CONT-EVT-002"]
    accepted = converges and ordered

    return result(
        "CONT-001",
        accepted,
        "partition_merge_replay_converges" if accepted else "partition_merge_diverged",
        merged,
        metrics(replay_converges=converges, recovery_deterministic=ordered),
    )


def replay_divergence_recovery() -> ContinuityScenarioResult:
    events = (
        ContinuityEvent(
            "CONT-EVT-003",
            "receipt:continuity-2",
            8,
            "node-a",
            1,
            "emit_receipt",
            {"decision": "ADMIT"},
            lineage=("known-root",),
        ),
        ContinuityEvent(
            "CONT-EVT-004",
            "receipt:continuity-2",
            8,
            "node-z",
            2,
            "forge_receipt",
            {"decision": "ADMIT", "forged": True},
            lineage=("forged-root",),
        ),
    )

    admitted = reject_invalid_lineage(events, {"known-root"})
    replay = reject_invalid_lineage(tuple(reversed(events)), {"known-root"})
    converges = continuity_hash_for(admitted) == continuity_hash_for(replay)
    recovered = len(admitted) == 1 and admitted[0].event_id == "CONT-EVT-003"
    accepted = converges and recovered

    return result(
        "CONT-002",
        accepted,
        "divergent_lineage_rejected" if accepted else "divergent_lineage_admitted",
        admitted,
        metrics(replay_converges=converges, recovery_deterministic=recovered),
    )


def identity_drift_resistance() -> ContinuityScenarioResult:
    aliases = {
        "driver:primary": "driver:canonical-1",
        "driver:offline-cache": "driver:canonical-1",
    }
    identities = (
        canonical_identity_for("driver:primary", aliases),
        canonical_identity_for("driver:offline-cache", aliases),
    )
    canonical_identity = identities[0]
    events = (
        ContinuityEvent(
            "CONT-EVT-005",
            canonical_identity,
            8,
            "node-a",
            1,
            "bind_driver",
            {"alias": "driver:primary"},
        ),
        ContinuityEvent(
            "CONT-EVT-006",
            identities[1],
            8,
            "node-b",
            2,
            "recover_driver",
            {"alias": "driver:offline-cache"},
        ),
    )

    preserved = len(set(identities)) == 1
    replay_converges = continuity_hash_for(events) == continuity_hash_for(tuple(reversed(events)))
    accepted = preserved and replay_converges

    return result(
        "CONT-003",
        accepted,
        "canonical_identity_preserved" if accepted else "identity_drift_detected",
        events,
        metrics(identity_preserved=preserved, replay_converges=replay_converges),
    )


def delayed_event_convergence() -> ContinuityScenarioResult:
    arrived_late = (
        ContinuityEvent(
            "CONT-EVT-008",
            "delivery:continuity-4",
            8,
            "node-b",
            2,
            "confirm_pickup",
            {"status": "picked_up"},
        ),
        ContinuityEvent(
            "CONT-EVT-007",
            "delivery:continuity-4",
            8,
            "node-a",
            1,
            "create_delivery",
            {"status": "created"},
        ),
    )
    canonical = tuple(reversed(arrived_late))
    converges = continuity_hash_for(arrived_late) == continuity_hash_for(canonical)
    accepted = converges

    return result(
        "CONT-004",
        accepted,
        "delayed_events_canonically_converge" if accepted else "delayed_event_divergence",
        arrived_late,
        metrics(replay_converges=converges, recovery_deterministic=converges),
    )


def coordination_rebuild() -> ContinuityScenarioResult:
    active_nodes = ("node-c", "node-a", "node-b")
    coordinator = deterministic_coordinator(active_nodes)
    replay_coordinator = deterministic_coordinator(reversed(active_nodes))
    events = (
        ContinuityEvent(
            "CONT-EVT-009",
            "coordination:continuity-5",
            8,
            coordinator,
            1,
            "elect_coordinator",
            {"coordinator": coordinator},
        ),
        ContinuityEvent(
            "CONT-EVT-010",
            "coordination:continuity-5",
            8,
            coordinator,
            2,
            "resume_coordination",
            {"status": "resumed"},
        ),
    )

    rebuilt = coordinator == replay_coordinator == "node-a"
    replay_converges = continuity_hash_for(events) == continuity_hash_for(tuple(reversed(events)))
    accepted = rebuilt and replay_converges

    return result(
        "CONT-005",
        accepted,
        "coordination_rebuilt_deterministically" if accepted else "coordination_rebuild_diverged",
        events,
        metrics(coordination_rebuilds=rebuilt, replay_converges=replay_converges),
    )


def offline_admissibility_rejoin() -> ContinuityScenarioResult:
    offline_events = (
        ContinuityEvent(
            "CONT-EVT-011",
            "market:continuity-6",
            8,
            "offline-node",
            1,
            "reserve_capacity",
            {"capacity": 1},
            offline_admissible=True,
        ),
        ContinuityEvent(
            "CONT-EVT-012",
            "market:continuity-6",
            8,
            "node-a",
            2,
            "confirm_capacity",
            {"status": "confirmed"},
            offline_admissible=True,
        ),
    )

    locally_admissible = all(event.offline_admissible for event in offline_events)
    replay_converges = continuity_hash_for(offline_events) == continuity_hash_for(
        tuple(reversed(offline_events))
    )
    accepted = locally_admissible and replay_converges

    return result(
        "CONT-006",
        accepted,
        "offline_execution_rejoined" if accepted else "offline_execution_rejected",
        offline_events,
        metrics(execution_admissible=locally_admissible, replay_converges=replay_converges),
    )


SCENARIOS = {
    "CONT-001": partition_survival,
    "CONT-002": replay_divergence_recovery,
    "CONT-003": identity_drift_resistance,
    "CONT-004": delayed_event_convergence,
    "CONT-005": coordination_rebuild,
    "CONT-006": offline_admissibility_rejoin,
}
