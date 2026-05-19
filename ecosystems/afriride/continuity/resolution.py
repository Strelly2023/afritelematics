from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

from ecosystems.afriride.runtime.commands import (
    AssignDriver,
    AssignDriverToRideA,
    AssignDriverToRideB,
    EmitAuditEvent,
    ReadRideState,
)
from ecosystems.afriride.runtime.execution.deterministic_executor import (
    DeterministicExecutor,
)
from ecosystems.afriride.runtime.state import RideState


Command = AssignDriver | AssignDriverToRideA | AssignDriverToRideB | EmitAuditEvent | ReadRideState


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_hash(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def initial_state() -> RideState:
    return RideState(
        drivers_available=frozenset({"A", "B"}),
        ride_status="OPEN",
        assigned_driver=None,
        ride_a_assigned=None,
        ride_b_assigned=None,
    )


def execute(
    commands: Iterable[Command],
    *,
    epoch: int = 6,
) -> dict[str, Any]:
    trace, final_state = DeterministicExecutor.execute_with_state(
        state=initial_state(),
        commands=tuple(commands),
        epoch=epoch,
    )
    return {
        "epoch": epoch,
        "trace": trace,
        "trace_hash": DeterministicExecutor.trace_hash(trace),
        "final_state": final_state.snapshot(),
        "state_hash": canonical_hash(final_state.snapshot()),
    }


def execution_receipt(
    *,
    scenario_id: str,
    execution: dict[str, Any],
    replay: dict[str, Any],
    identity_refs: Iterable[str],
    transcript: Iterable[dict[str, Any]],
    mutation_trace: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema": "ecosystems.afriride.continuity.receipt.v1",
        "scenario_id": scenario_id,
        "execution_hash": execution["trace_hash"],
        "replay_hash": replay["trace_hash"],
        "state_hash": execution["state_hash"],
        "identity_hash": canonical_hash(sorted(identity_refs)),
        "transcript_hash": canonical_hash(tuple(transcript)),
        "mutation_trace_hash": canonical_hash(tuple(mutation_trace)),
        "epoch": execution["epoch"],
    }


def receipt_hash(receipt: dict[str, Any]) -> str:
    return canonical_hash(receipt)


def trace_has_refusal(trace: Iterable[dict[str, Any]]) -> bool:
    return any(step.get("type") == "REFUSAL" for step in trace)


def transcript_from_trace(trace: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "index": index,
            "step": dict(step),
        }
        for index, step in enumerate(trace)
    )


def mutation_trace_from_execution(execution: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return (
        {
            "state_hash": execution["state_hash"],
            "trace_hash": execution["trace_hash"],
            "final_state": execution["final_state"],
        },
    )


def epoch_chain_hash(executions: Iterable[dict[str, Any]]) -> str:
    chain = []
    previous = "GENESIS"

    for execution in sorted(executions, key=lambda item: item["epoch"]):
        current = canonical_hash(
            {
                "previous": previous,
                "epoch": execution["epoch"],
                "trace_hash": execution["trace_hash"],
                "state_hash": execution["state_hash"],
            }
        )
        chain.append(current)
        previous = current

    return canonical_hash(chain)
