from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Dict, List

from afritech.distributed.consensus.consensus_engine import ProofConsensusEngine
from afritech.distributed.proof import hash_result
from afritech.distributed.trust.scoring import CONSENSUS_MATCH, CONSENSUS_MISMATCH
from afritech.distributed.trust.trust_engine import TrustEngine
from afritech.runtime.audit.ledger import AuditLedger


def simulate_twenty_node_adversarial_network() -> Dict[str, Any]:
    nodes = [f"node-{index:02d}" for index in range(20)]
    adversaries = {"node-03", "node-07", "node-11", "node-19"}
    honest_result = {"contract": "scale.demo", "value": 144}
    malicious_result = {"contract": "scale.demo", "value": -1}

    proofs = [
        _proof(
            node_id=node,
            result=malicious_result if node in adversaries else honest_result,
        )
        for node in nodes
    ]

    consensus = ProofConsensusEngine().decide(proofs, total_nodes=len(nodes))
    accepted_nodes = set(consensus.node_ids)

    trust = TrustEngine()
    for proof in proofs:
        node_id = proof["node"]
        if node_id in accepted_nodes:
            trust.record_event(node_id, CONSENSUS_MATCH)
        else:
            trust.record_event(node_id, CONSENSUS_MISMATCH)

    ledger = AuditLedger()
    block = ledger.commit_block(consensus.proofs)
    trust_snapshot = trust.snapshot()

    payload = {
        "schema": "afritech.twenty_node_adversarial_network.v1",
        "node_count": len(nodes),
        "adversarial_nodes": sorted(adversaries),
        "accepted_nodes": sorted(accepted_nodes),
        "rejected_nodes": sorted(set(nodes) - accepted_nodes),
        "consensus": consensus.to_dict(),
        "chain_valid": ledger.verify_chain(),
        "block_hash": block.hash,
        "trust": trust_snapshot,
        "passed": (
            consensus.result == honest_result
            and consensus.votes == 16
            and set(nodes) - accepted_nodes == adversaries
            and ledger.verify_chain()
            and all(trust_snapshot[node]["trust_score"] < 100 for node in adversaries)
        ),
    }
    payload["evidence_hash"] = _canonical_hash(payload)
    return payload


def _proof(node_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "node": node_id,
        "result": result,
        "hash": hash_result(result),
        "signature": "00",
        "metadata": {"contract_id": "scale.demo", "epoch": 0},
    }


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
