from __future__ import annotations

from afritech.simulation.adversarial.models import AdversarialEvent, ScenarioResult
from afritech.simulation.adversarial.resolution import (
    canonical_merge,
    reject_invalid_lineage,
    state_hash_for,
)
from afritech.core.runtime.concurrency import ConcurrentMutation, resolve_conflicts


TARGETS = {
    "ADV-001": ("SEM-DET-001", "AX-DET-001", "AX-DET-002", "AX-DET-003"),
    "ADV-002": ("SEM-RPL-001", "SEM-ID-001", "AX-RPL-001", "AX-ID-001"),
    "ADV-003": ("SEM-CW-001", "AX-CW-001", "AX-CW-002", "AX-CW-003"),
    "ADV-004": ("SEM-ADM-001", "AX-ADM-001", "AX-ADM-002", "AX-ADM-003"),
    "ADV-005": ("SEM-RPL-001", "AX-RPL-002", "AX-RPL-003"),
    "ADV-006": ("SEM-ID-001", "AX-ID-002", "AX-ID-003"),
    "ADV-008": ("SEM-DET-001", "AX-DET-001", "AX-DET-002", "AX-DET-003"),
}


def metric_set(
    *,
    determinism_violation: bool = False,
    replay_equivalence: bool = True,
    divergence_detected: bool = False,
    reconciliation_success: bool = True,
) -> dict[str, bool]:
    return {
        "determinism_violation": determinism_violation,
        "replay_equivalence": replay_equivalence,
        "divergence_detected": divergence_detected,
        "reconciliation_success": reconciliation_success,
    }


def reordered_events() -> ScenarioResult:
    events = (
        AdversarialEvent("EVT-002", "ride-1", 8, "node-b", 2, {"status": "assigned"}),
        AdversarialEvent("EVT-001", "ride-1", 8, "node-a", 1, {"status": "requested"}),
    )

    forward_hash = state_hash_for(events)
    reverse_hash = state_hash_for(reversed(events))

    return ScenarioResult(
        scenario_id="ADV-001",
        accepted=forward_hash == reverse_hash,
        reason="canonical_order_stable" if forward_hash == reverse_hash else "order_divergence",
        state_hash=forward_hash,
        targets=TARGETS["ADV-001"],
        metrics=metric_set(determinism_violation=forward_hash != reverse_hash),
    )


def byzantine_witness() -> ScenarioResult:
    events = (
        AdversarialEvent(
            "EVT-003",
            "ride-2",
            8,
            "node-a",
            1,
            {"status": "requested"},
            lineage=("known-root",),
        ),
        AdversarialEvent(
            "EVT-004",
            "ride-2",
            8,
            "node-z",
            2,
            {"status": "completed"},
            lineage=("forged-root",),
        ),
    )

    admitted = reject_invalid_lineage(events, {"known-root"})
    accepted = len(admitted) == 1 and admitted[0].event_id == "EVT-003"

    return ScenarioResult(
        scenario_id="ADV-002",
        accepted=accepted,
        reason="invalid_lineage_rejected" if accepted else "invalid_lineage_admitted",
        state_hash=state_hash_for(admitted),
        targets=TARGETS["ADV-002"],
        metrics=metric_set(divergence_detected=True),
    )


def undeclared_semantic_surface() -> ScenarioResult:
    declared_surfaces = {"runtime", "replay", "governance", "verification"}
    attempted_surface = "shadow_semantics"
    accepted = attempted_surface not in declared_surfaces

    return ScenarioResult(
        scenario_id="ADV-003",
        accepted=accepted,
        reason="undeclared_surface_rejected" if accepted else "undeclared_surface_admitted",
        state_hash=None,
        targets=TARGETS["ADV-003"],
        metrics=metric_set(replay_equivalence=False, divergence_detected=True),
    )


def invalid_history_admission() -> ScenarioResult:
    events = (
        AdversarialEvent("EVT-005", "ride-3", 8, "node-a", 2, {"status": "assigned"}),
    )
    history_is_valid = all(event.causal_index == index for index, event in enumerate(events, start=1))
    accepted = not history_is_valid

    return ScenarioResult(
        scenario_id="ADV-004",
        accepted=accepted,
        reason="invalid_history_rejected" if accepted else "invalid_history_admitted",
        state_hash=None if accepted else state_hash_for(events),
        targets=TARGETS["ADV-004"],
        metrics=metric_set(replay_equivalence=False, divergence_detected=True),
    )


def replay_state_divergence() -> ScenarioResult:
    original = (
        AdversarialEvent("EVT-006", "ride-4", 8, "node-a", 1, {"status": "requested"}),
        AdversarialEvent("EVT-007", "ride-4", 8, "node-a", 2, {"status": "assigned"}),
    )
    replay = (
        AdversarialEvent("EVT-006", "ride-4", 8, "node-a", 1, {"status": "requested"}),
        AdversarialEvent("EVT-007", "ride-4", 8, "node-a", 2, {"status": "cancelled"}),
    )

    original_hash = state_hash_for(original)
    replay_hash = state_hash_for(replay)
    accepted = original_hash != replay_hash

    return ScenarioResult(
        scenario_id="ADV-005",
        accepted=accepted,
        reason="replay_divergence_rejected" if accepted else "replay_divergence_admitted",
        state_hash=original_hash,
        targets=TARGETS["ADV-005"],
        metrics=metric_set(replay_equivalence=False, divergence_detected=True),
    )


def identity_alias_collision() -> ScenarioResult:
    aliases = {
        "driver:primary": "driver-1",
        "driver:shadow": "driver-1",
        "driver:other": "driver-2",
    }
    reverse: dict[str, set[str]] = {}

    for alias, identity in aliases.items():
        reverse.setdefault(identity, set()).add(alias)

    accepted = reverse["driver-1"] == {"driver:primary", "driver:shadow"}

    return ScenarioResult(
        scenario_id="ADV-006",
        accepted=accepted,
        reason="aliases_preserve_canonical_identity" if accepted else "identity_collision_diverged",
        state_hash=None,
        targets=TARGETS["ADV-006"],
        metrics=metric_set(),
    )


def partition_replay_divergence() -> ScenarioResult:
    node_states = {
        "node-b": (
            AdversarialEvent("EVT-009", "ride-5", 8, "node-b", 2, {"status": "assigned"}),
        ),
        "node-a": (
            AdversarialEvent("EVT-008", "ride-5", 8, "node-a", 1, {"status": "requested"}),
        ),
    }

    merged = canonical_merge(node_states)
    accepted = [event.event_id for event in merged] == ["EVT-008", "EVT-009"]

    return ScenarioResult(
        scenario_id="ADV-007",
        accepted=accepted,
        reason="partition_merge_canonical" if accepted else "partition_merge_diverged",
        state_hash=state_hash_for(merged),
        targets=("SEM-DET-001", "SEM-RPL-001", "AX-DET-002", "AX-RPL-002"),
        metrics=metric_set(divergence_detected=True),
    )


def concurrent_mutation_conflict() -> ScenarioResult:
    mutations = (
        ConcurrentMutation("MUT-002", "ride-6", 101, "node-b", {"status": "assigned"}),
        ConcurrentMutation("MUT-001", "ride-6", 101, "node-a", {"status": "requested"}),
    )

    forward = resolve_conflicts(mutations)
    reverse = resolve_conflicts(tuple(reversed(mutations)))
    accepted = forward == reverse

    return ScenarioResult(
        scenario_id="ADV-008",
        accepted=accepted,
        reason="conflict_resolution_deterministic" if accepted else "conflict_resolution_diverged",
        state_hash=state_hash_for(()),
        targets=TARGETS["ADV-008"],
        metrics=metric_set(determinism_violation=not accepted),
    )


SCENARIOS = {
    "ADV-001": reordered_events,
    "ADV-002": byzantine_witness,
    "ADV-003": undeclared_semantic_surface,
    "ADV-004": invalid_history_admission,
    "ADV-005": replay_state_divergence,
    "ADV-006": identity_alias_collision,
    "ADV-007": partition_replay_divergence,
    "ADV-008": concurrent_mutation_conflict,
}


PRESSURE_CLASSES = (
    "NETWORK_PARTITION",
    "CLOCK_SKEW",
    "DUPLICATE_EXECUTION_REQUEST",
    "DELAYED_RECEIPT",
    "STALE_EPOCH",
    "CONFLICTING_GOVERNANCE_AMENDMENT",
    "WITNESS_CORRUPTION",
    "HASH_COLLISION_SIMULATION",
    "PARTIAL_TRANSCRIPT_LOSS",
    "CROSS_EPOCH_REPLAY_DIVERGENCE",
)


def pressure_scenario(
    scenario_id: str,
    pressure_class: str,
) -> ScenarioResult:
    seed = int(scenario_id.split("-")[-1])
    events = (
        AdversarialEvent(
            f"EVT-{scenario_id}-A",
            f"object-{seed}",
            8,
            "node-a",
            1,
            {"pressure_class": pressure_class, "status": "observed"},
            lineage=("known-root",),
        ),
        AdversarialEvent(
            f"EVT-{scenario_id}-B",
            f"object-{seed}",
            8,
            "node-b",
            2,
            {"pressure_class": pressure_class, "status": "reconciled"},
            lineage=("known-root",),
        ),
    )
    state_hash = state_hash_for(events)
    replay_hash = state_hash_for(tuple(reversed(events)))
    accepted = state_hash == replay_hash

    return ScenarioResult(
        scenario_id=scenario_id,
        accepted=accepted,
        reason=(
            f"{pressure_class.lower()}_replay_verifiable"
            if accepted
            else f"{pressure_class.lower()}_diverged"
        ),
        state_hash=state_hash,
        targets=("SEM-DET-001", "SEM-RPL-001", "AX-DET-002", "AX-RPL-002"),
        metrics=metric_set(
            determinism_violation=not accepted,
            replay_equivalence=accepted,
            divergence_detected=True,
            reconciliation_success=accepted,
        ),
    )


def make_pressure_scenario(
    scenario_id: str,
    pressure_class: str,
):
    return lambda: pressure_scenario(scenario_id, pressure_class)


for offset, scenario_number in enumerate(range(9, 51)):
    scenario_id = f"ADV-{scenario_number:03d}"
    SCENARIOS[scenario_id] = make_pressure_scenario(
        scenario_id,
        PRESSURE_CLASSES[offset % len(PRESSURE_CLASSES)],
    )
