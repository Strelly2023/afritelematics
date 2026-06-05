from __future__ import annotations

from typing import Any, Dict, List

from afritech.distributed.consensus.consensus_engine import ProofConsensusEngine
from afritech.distributed.consensus.validator import ProofValidator
from afritech.distributed.proof import hash_result
from afritech.distributed.state.state_machine import LedgerStateMachine
from afritech.distributed.trust.scoring import (
    CONSENSUS_MATCH,
    CONSENSUS_MISMATCH,
    INVALID_PROOF,
)
from afritech.distributed.trust.trust_engine import TrustEngine
from afritech.runtime.audit.ledger import AuditLedger


def build_structural_proof(
    node_id: str,
    result: Any,
    contract_id: str = "contract.demo",
    epoch: int = 0,
) -> Dict[str, Any]:
    return {
        "node": node_id,
        "result": result,
        "hash": hash_result(result),
        "signature": "00",
        "metadata": {
            "contract_id": contract_id,
            "epoch": epoch,
        },
    }


def run_five_node_validation() -> Dict[str, Any]:
    result = {"value": 42}
    proofs = [
        build_structural_proof(f"node-{index}", result)
        for index in range(5)
    ]

    consensus = ProofConsensusEngine().decide(proofs, total_nodes=5)
    ledger = AuditLedger()
    block = ledger.commit_block(consensus.proofs)

    state_machine = LedgerStateMachine()
    state = state_machine.replay_ledger(ledger)

    return {
        "consensus": consensus.to_dict(),
        "block": block.to_dict(),
        "chain_valid": ledger.verify_chain(),
        "state": state,
    }


def run_malicious_node_validation() -> Dict[str, Any]:
    honest_result = {"value": 42}
    malicious_result = {"value": 7}

    proofs = [
        build_structural_proof("node-a", honest_result),
        build_structural_proof("node-b", honest_result),
        build_structural_proof("node-c", honest_result),
        build_structural_proof("node-d", honest_result),
        build_structural_proof("node-malicious", malicious_result),
        {
            "node": "node-tampered",
            "result": honest_result,
            "hash": "tampered",
            "signature": "00",
            "metadata": {"contract_id": "contract.demo", "epoch": 0},
        },
    ]

    validator = ProofValidator()
    valid_proofs: List[Dict[str, Any]] = []
    trust = TrustEngine()

    for proof in proofs:
        node_id = str(proof.get("node", "unknown"))
        if validator.validate(proof):
            valid_proofs.append(proof)
        else:
            trust.record_event(node_id, INVALID_PROOF)

    consensus = ProofConsensusEngine().decide(valid_proofs, total_nodes=5)
    accepted_nodes = set(consensus.node_ids)

    for proof in valid_proofs:
        node_id = proof["node"]
        if node_id in accepted_nodes:
            trust.record_event(node_id, CONSENSUS_MATCH)
        else:
            trust.record_event(node_id, CONSENSUS_MISMATCH)

    ledger = AuditLedger()
    block = ledger.commit_block(consensus.proofs)

    return {
        "consensus": consensus.to_dict(),
        "block": block.to_dict(),
        "chain_valid": ledger.verify_chain(),
        "trust": trust.snapshot(),
        "accepted_nodes": sorted(accepted_nodes),
    }
