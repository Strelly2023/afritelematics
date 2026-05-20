from copy import deepcopy

import yaml

from afritech.core.runtime.receipts import (
    receipt_inspection_hash,
    reconstruct_receipt_bundle,
    verify_receipt_bundle,
)
from afritech.core.runtime.system_enforcement.execution_guard import (
    admit_contract,
    truth_values_from_payload,
)


CONTRACT_ROOT = "afritech/semantic_engine/contracts"


def load_contract(name: str) -> dict:
    with open(f"{CONTRACT_ROOT}/{name}", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    assert isinstance(payload, dict)
    return payload


def test_admitted_decision_emits_complete_receipt_bundle():
    contract = load_contract("minimal_admit.yaml")
    result = admit_contract(contract)

    assert result["status"] == "ADMIT"
    assert result["receipt"]["decision"] == "ADMIT"
    assert result["receipt"]["execution_chain_hash"]
    assert result["receipt"]["deterministic_execution_chain"] is True
    assert result["receipt"]["transcript_hash"]
    assert result["receipt"]["mutation_trace_hash"]
    assert result["receipt"]["replay_hash"]
    assert result["receipt"]["inspection_hash"]
    assert result["receipt"]["signature"]
    assert result["transcript"]["execution_chain_hash"] == result["receipt"]["execution_chain_hash"]
    assert result["mutation_trace"]["mutation_trace_hash"] == result["receipt"]["mutation_trace_hash"]
    assert verify_receipt_bundle(result) is True


def test_denied_decision_is_receipt_bound_and_reconstructable():
    contract = load_contract("adversarial_rejected_admission.yaml")
    truth_values = truth_values_from_payload(contract)
    result = admit_contract(contract, truth_values=truth_values)

    rebuilt = reconstruct_receipt_bundle(
        contract=contract,
        truth_values=truth_values,
        result=result,
        inspection_hash=receipt_inspection_hash(result),
    )

    assert result["status"] == "DENY"
    assert result["receipt"]["decision"] == "DENY"
    assert rebuilt["receipt"]["receipt_hash"] == result["receipt"]["receipt_hash"]
    assert verify_receipt_bundle(rebuilt) is True


def test_tampered_receipt_bundle_fails_closed():
    contract = load_contract("minimal_admit.yaml")
    result = admit_contract(contract)

    tampered = deepcopy(result)
    tampered["transcript"]["steps"][-1]["decision"] = "DENY"

    assert verify_receipt_bundle(tampered) is False
