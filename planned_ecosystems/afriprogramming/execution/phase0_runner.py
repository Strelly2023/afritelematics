"""AfriProgramming Phase 0 runner.

Execution generates behavior.
Replay authorizes truth.
"""

from __future__ import annotations

from pprint import pprint

from afritech.core.runtime.context.runtime_context import RuntimeContext
from afritech.core.runtime.engine.executor import ExecutionEngine
from afritech.runtime.replay.replay_engine import replay
from afritech.proof.witness.execution_witness import generate_witness
from afritech.proof.constitutional_receipt import generate_receipt

from ecosystems.afriprogramming.execution.sandbox import run_user_function


SURFACE = "ecosystems.afriprogramming.execution.sandbox"


def execution_fn(payload):
    value = payload["payload"]["x"]
    result = run_user_function(value)

    return {
        "input": value,
        "output": result,
    }


def main() -> dict[str, object]:
    context = RuntimeContext(
        authority_profile="phase0",
        payload={
            "x": 5,
        },
        replay_requirements={
            "deterministic": True,
        },
    )

    engine = ExecutionEngine(
        execution_fn=execution_fn,
    )

    result = engine.execute(context)

    if not result.success:
        raise RuntimeError(result.error)

    trace = {
        "surface": SURFACE,
        "input": 5,
        "output": result.output["output"],
        "hash": result.result_hash,
    }

    replay_verified = replay(
        run_user_function,
        trace,
    )

    witness = generate_witness(trace)

    receipt = generate_receipt(
        trace=trace,
        witness=witness,
        replay_verified=replay_verified,
    )

    final = {
        "trace": trace,
        "replay_verified": replay_verified,
        "witness": witness,
        "receipt": receipt,
    }

    print("✅ Phase 0 runtime execution complete")
    pprint(final)

    return final


if __name__ == "__main__":
    main()