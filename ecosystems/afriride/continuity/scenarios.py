from __future__ import annotations

from ecosystems.afriride.continuity.models import AfriRideContinuityResult
from ecosystems.afriride.continuity.resolution import (
    epoch_chain_hash,
    execute,
    execution_receipt,
    mutation_trace_from_execution,
    receipt_hash,
    trace_has_refusal,
    transcript_from_trace,
)
from ecosystems.afriride.runtime.commands import (
    AssignDriver,
    AssignDriverToRideA,
    AssignDriverToRideB,
    EmitAuditEvent,
    ReadRideState,
)


REQUIRED_METRICS = (
    "replay_equivalent",
    "identity_continuity",
    "coordination_continuity",
    "authority_conflict_prevented",
    "reconstruction_complete",
    "epoch_replay_stable",
)


TARGETS = {
    "AFRIRIDE-CONT-001": (
        "connectivity_loss_recovery",
        "SEM-RPL-001",
        "SEM-ID-001",
        "AX-RPL-002",
    ),
    "AFRIRIDE-CONT-002": (
        "replay_reconstruction",
        "SEM-RPL-001",
        "AX-RPL-002",
        "trace_complete",
    ),
    "AFRIRIDE-CONT-003": (
        "adversarial_coordination",
        "SEM-DET-001",
        "SEM-ADM-001",
        "AX-ADM-003",
    ),
    "AFRIRIDE-CONT-004": (
        "offline_operational_continuity",
        "SEM-RPL-001",
        "SEM-ID-001",
        "AX-ID-003",
    ),
    "AFRIRIDE-CONT-005": (
        "multi_epoch_recovery",
        "SEM-DET-001",
        "SEM-RPL-001",
        "AX-DET-002",
    ),
}


def metrics(
    *,
    replay_equivalent: bool = True,
    identity_continuity: bool = True,
    coordination_continuity: bool = True,
    authority_conflict_prevented: bool = True,
    reconstruction_complete: bool = True,
    epoch_replay_stable: bool = True,
) -> dict[str, bool]:
    return {
        "replay_equivalent": replay_equivalent,
        "identity_continuity": identity_continuity,
        "coordination_continuity": coordination_continuity,
        "authority_conflict_prevented": authority_conflict_prevented,
        "reconstruction_complete": reconstruction_complete,
        "epoch_replay_stable": epoch_replay_stable,
    }


def build_result(
    scenario_id: str,
    accepted: bool,
    reason: str,
    execution: dict[str, object],
    replay: dict[str, object],
    scenario_metrics: dict[str, bool],
    identities: tuple[str, ...],
) -> AfriRideContinuityResult:
    transcript = transcript_from_trace(execution["trace"])
    mutation_trace = mutation_trace_from_execution(execution)
    receipt = execution_receipt(
        scenario_id=scenario_id,
        execution=execution,
        replay=replay,
        identity_refs=identities,
        transcript=transcript,
        mutation_trace=mutation_trace,
    )
    return AfriRideContinuityResult(
        scenario_id=scenario_id,
        accepted=accepted,
        reason=reason,
        receipt_hash=receipt_hash(receipt),
        targets=TARGETS[scenario_id],
        metrics=scenario_metrics,
    )


def connectivity_loss_recovery() -> AfriRideContinuityResult:
    partition_a = (
        ReadRideState("rider-request-cache"),
        AssignDriver("A", epoch=6),
    )
    partition_b = (
        EmitAuditEvent("driver-offline-heartbeat"),
        AssignDriver("A", epoch=6),
    )

    execution = execute(partition_a)
    replay = execute(tuple(reversed(partition_b)))
    replay_equivalent = execution["trace_hash"] == replay["trace_hash"]
    identity_continuity = execution["final_state"]["assigned_driver"] == "A"
    coordination_continuity = execution["final_state"] == replay["final_state"]
    accepted = replay_equivalent and identity_continuity and coordination_continuity

    return build_result(
        "AFRIRIDE-CONT-001",
        accepted,
        "connectivity_loss_recovered" if accepted else "connectivity_loss_diverged",
        execution,
        replay,
        metrics(
            replay_equivalent=replay_equivalent,
            identity_continuity=identity_continuity,
            coordination_continuity=coordination_continuity,
        ),
        ("driver:A", "rider:request-cache"),
    )


def replay_reconstruction() -> AfriRideContinuityResult:
    commands = (
        ReadRideState("dispute-read"),
        EmitAuditEvent("payment-lineage-observed"),
        AssignDriver("B", epoch=6),
    )
    execution = execute(commands)
    replay = execute(tuple(reversed(commands)))
    transcript = transcript_from_trace(execution["trace"])
    mutation_trace = mutation_trace_from_execution(execution)
    reconstruction_complete = bool(transcript) and bool(mutation_trace)
    replay_equivalent = execution["trace_hash"] == replay["trace_hash"]
    accepted = replay_equivalent and reconstruction_complete

    return build_result(
        "AFRIRIDE-CONT-002",
        accepted,
        "trip_reconstruction_complete" if accepted else "trip_reconstruction_incomplete",
        execution,
        replay,
        metrics(
            replay_equivalent=replay_equivalent,
            reconstruction_complete=reconstruction_complete,
        ),
        ("driver:B", "payment:lineage"),
    )


def adversarial_coordination() -> AfriRideContinuityResult:
    commands = (
        AssignDriver("B", epoch=6),
        AssignDriver("A", epoch=6),
    )
    execution = execute(commands)
    replay = execute(tuple(reversed(commands)))
    replay_equivalent = execution["trace_hash"] == replay["trace_hash"]
    authority_conflict_prevented = trace_has_refusal(execution["trace"])
    coordination_continuity = execution["final_state"] == replay["final_state"]
    accepted = replay_equivalent and authority_conflict_prevented and coordination_continuity

    return build_result(
        "AFRIRIDE-CONT-003",
        accepted,
        "duplicate_ride_authority_rejected" if accepted else "duplicate_ride_authority_admitted",
        execution,
        replay,
        metrics(
            replay_equivalent=replay_equivalent,
            coordination_continuity=coordination_continuity,
            authority_conflict_prevented=authority_conflict_prevented,
        ),
        ("driver:A", "driver:B", "ride:single-authority"),
    )


def offline_operational_continuity() -> AfriRideContinuityResult:
    offline_first = (
        EmitAuditEvent("offline-driver-presence"),
        AssignDriverToRideA("A", epoch=6),
        AssignDriverToRideB("B", epoch=6),
    )
    online_rejoin = (
        AssignDriverToRideB("B", epoch=6),
        ReadRideState("offline-rejoin-read"),
        AssignDriverToRideA("A", epoch=6),
    )
    execution = execute(offline_first)
    replay = execute(online_rejoin)
    replay_equivalent = execution["trace_hash"] == replay["trace_hash"]
    identity_continuity = (
        execution["final_state"]["ride_a_assigned"] == "A"
        and execution["final_state"]["ride_b_assigned"] == "B"
    )
    coordination_continuity = execution["final_state"] == replay["final_state"]
    accepted = replay_equivalent and identity_continuity and coordination_continuity

    return build_result(
        "AFRIRIDE-CONT-004",
        accepted,
        "offline_operations_rejoined" if accepted else "offline_operations_diverged",
        execution,
        replay,
        metrics(
            replay_equivalent=replay_equivalent,
            identity_continuity=identity_continuity,
            coordination_continuity=coordination_continuity,
        ),
        ("driver:A", "driver:B", "offline:rejoin"),
    )


def multi_epoch_recovery() -> AfriRideContinuityResult:
    epoch_6 = execute((AssignDriver("A", epoch=6),), epoch=6)
    epoch_6_replay = execute((AssignDriver("A", epoch=6),), epoch=6)
    epoch_7 = execute(
        (
            AssignDriverToRideA("A", epoch=7),
            AssignDriverToRideB("B", epoch=7),
        ),
        epoch=7,
    )
    epoch_7_replay = execute(
        (
            AssignDriverToRideB("B", epoch=7),
            AssignDriverToRideA("A", epoch=7),
        ),
        epoch=7,
    )
    chain_hash = epoch_chain_hash((epoch_6, epoch_7))
    replay_chain_hash = epoch_chain_hash((epoch_6_replay, epoch_7_replay))
    replay_equivalent = (
        epoch_6["trace_hash"] == epoch_6_replay["trace_hash"]
        and epoch_7["trace_hash"] == epoch_7_replay["trace_hash"]
    )
    epoch_replay_stable = chain_hash == replay_chain_hash
    accepted = replay_equivalent and epoch_replay_stable

    return build_result(
        "AFRIRIDE-CONT-005",
        accepted,
        "multi_epoch_recovery_stable" if accepted else "multi_epoch_recovery_diverged",
        epoch_7,
        epoch_7_replay,
        metrics(
            replay_equivalent=replay_equivalent,
            epoch_replay_stable=epoch_replay_stable,
        ),
        ("epoch:6", "epoch:7", "driver:A", "driver:B"),
    )


SCENARIOS = {
    "AFRIRIDE-CONT-001": connectivity_loss_recovery,
    "AFRIRIDE-CONT-002": replay_reconstruction,
    "AFRIRIDE-CONT-003": adversarial_coordination,
    "AFRIRIDE-CONT-004": offline_operational_continuity,
    "AFRIRIDE-CONT-005": multi_epoch_recovery,
}
