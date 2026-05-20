from copy import deepcopy

import yaml
import pytest

from afritech.core.runtime.system_enforcement.execution_guard import admit_contract
from afritech.trace.trace_reconstructor import (
    TraceReconstructionError,
    TraceReconstructor,
)


CONTRACT = "afritech/semantic_engine/contracts/minimal_admit.yaml"


def test_receipt_bundle_reconstructs_from_artifacts_only():
    with open(CONTRACT, encoding="utf-8") as handle:
        contract = yaml.safe_load(handle)

    result = admit_contract(contract)
    reconstructed = TraceReconstructor.reconstruct_receipt_bundle(result)

    assert reconstructed["status"] == "RECONSTRUCTED"
    assert reconstructed["receipt_hash"] == result["receipt"]["receipt_hash"]
    assert reconstructed["replay_hash"] == result["receipt"]["replay_hash"]
    assert reconstructed["transcript_hash"] == result["receipt"]["transcript_hash"]
    assert reconstructed["mutation_trace_hash"] == result["receipt"]["mutation_trace_hash"]


def test_trace_reconstruction_rejects_tampered_transcript():
    with open(CONTRACT, encoding="utf-8") as handle:
        contract = yaml.safe_load(handle)

    result = admit_contract(contract)
    tampered = deepcopy(result)
    tampered["transcript"]["steps"][-1]["decision"] = "DENY"

    with pytest.raises(TraceReconstructionError):
        TraceReconstructor.reconstruct_receipt_bundle(tampered)
