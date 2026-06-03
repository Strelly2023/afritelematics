"""AfriProgramming Phase 0 runner.

Execution generates behavior.
Replay authorizes truth.
"""

from __future__ import annotations

from pprint import pprint

from afritech.runtime.admission.admission_engine import RuntimeAdmissionEngine
from afritech.core.runtime.engine.executor import ExecutionEngine
from afritech.runtime.replay.replay_engine import replay
from afritech.proof.witness.execution_witness import generate_witness
from afritech.proof.constitutional_receipt import generate_receipt


SURFACE = "afritech.ecosystems.afriprogramming.execution.sandbox"
CERTIFICATE_PATH = "afritech/proof/certificates/runtime_epoch_0006.cert"
EPOCH = 6


def user_function(x: int) -> int:
    return x * 2


def run() -> dict[str, object]:
    admission = RuntimeAdmissionEngine(
        certificate_path=CERTIFICATE_PATH,
        expected_epoch=EPOCH,
    ).admit()

    engine = ExecutionEngine(surface=SURFACE)
    trace = engine.run(user_function, 5)

    replay_verified = replay(user_function, trace)

    witness = generate_witness(trace)

    receipt = generate_receipt(
        trace=trace,
        witness=witness,
        replay_verified=replay_verified,
    )

    return {
        "admission": admission.canonical_dict(),
        "trace": trace,
        "replay_verified": replay_verified,
        "witness": witness,
        "receipt": receipt,
    }


if __name__ == "__main__":
    pprint(run())