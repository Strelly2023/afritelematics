from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Dict, List

from afritech.distributed.consensus.consensus_engine import ProofConsensusEngine
from afritech.distributed.consensus.errors import QuorumNotReached
from afritech.distributed.consensus.validator import ProofValidator
from afritech.distributed.proof import hash_result
from afritech.distributed.trust.scoring import CONSENSUS_MISMATCH, INVALID_PROOF
from afritech.distributed.trust.trust_engine import TrustEngine
from afritech.runtime.audit.ledger import AuditLedger


@dataclass(frozen=True)
class AttackResult:
    attack: str
    detected: bool
    rejected: bool
    trust_penalized: bool
    evidence: Dict[str, Any]

    @property
    def passed(self) -> bool:
        return self.detected and self.rejected and self.trust_penalized

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attack": self.attack,
            "detected": self.detected,
            "rejected": self.rejected,
            "trust_penalized": self.trust_penalized,
            "passed": self.passed,
            "evidence": self.evidence,
        }


def run_adversarial_attack_simulation_suite() -> Dict[str, Any]:
    attacks = [
        _tampered_hash_attack(),
        _wrong_result_minority_attack(),
        _metadata_tampering_attack(),
        _replay_duplicate_attack(),
        _quorum_failure_attack(),
    ]
    payload = {
        "schema": "afritech.adversarial_attack_suite.v1",
        "passed": all(attack.passed for attack in attacks),
        "attacks": [attack.to_dict() for attack in attacks],
    }
    payload["evidence_hash"] = _canonical_hash(payload)
    return payload


def _tampered_hash_attack() -> AttackResult:
    proof = _proof("node-attacker", {"value": 42})
    proof["hash"] = "bad-hash"
    validator = ProofValidator()
    trust = TrustEngine()
    valid = validator.validate(proof)
    if not valid:
        trust.record_event("node-attacker", INVALID_PROOF)
    score = trust.snapshot()["node-attacker"]["trust_score"]
    return AttackResult(
        attack="tampered_hash",
        detected=not valid,
        rejected=not valid,
        trust_penalized=score < 100,
        evidence={"validator_accepted": valid, "trust_score": score},
    )


def _wrong_result_minority_attack() -> AttackResult:
    honest_result = {"value": 42}
    wrong_result = {"value": 1000}
    proofs = [
        _proof("node-a", honest_result),
        _proof("node-b", honest_result),
        _proof("node-c", honest_result),
        _proof("node-d", honest_result),
        _proof("node-attacker", wrong_result),
    ]
    consensus = ProofConsensusEngine().decide(proofs, total_nodes=5)
    trust = TrustEngine()
    for proof in proofs:
        if proof["node"] not in consensus.node_ids:
            trust.record_event(proof["node"], CONSENSUS_MISMATCH)
    score = trust.snapshot()["node-attacker"]["trust_score"]
    ledger = AuditLedger()
    ledger.commit_block(consensus.proofs)
    return AttackResult(
        attack="wrong_result_minority",
        detected="node-attacker" not in consensus.node_ids,
        rejected=consensus.result == honest_result and ledger.verify_chain(),
        trust_penalized=score < 100,
        evidence={
            "accepted_nodes": consensus.node_ids,
            "attacker_score": score,
            "chain_valid": ledger.verify_chain(),
        },
    )


def _metadata_tampering_attack() -> AttackResult:
    proof = _proof("node-attacker", {"value": 42})
    proof["metadata"] = {"contract_id": None, "epoch": "tampered"}
    invalid_metadata = not isinstance(proof["metadata"].get("contract_id"), str)
    trust = TrustEngine()
    if invalid_metadata:
        trust.record_event("node-attacker", INVALID_PROOF)
    score = trust.snapshot()["node-attacker"]["trust_score"]
    return AttackResult(
        attack="metadata_tampering",
        detected=invalid_metadata,
        rejected=invalid_metadata,
        trust_penalized=score < 100,
        evidence={"attacker_score": score},
    )


def _replay_duplicate_attack() -> AttackResult:
    result = {"value": 42}
    duplicate = _proof("node-attacker", result)
    proofs = [
        _proof("node-a", result),
        _proof("node-b", result),
        _proof("node-c", result),
        duplicate,
        dict(duplicate),
    ]
    unique_nodes = {proof["node"] for proof in proofs}
    duplicate_detected = len(unique_nodes) < len(proofs)
    trust = TrustEngine()
    if duplicate_detected:
        trust.record_event("node-attacker", INVALID_PROOF)
    consensus = ProofConsensusEngine().decide(proofs, total_nodes=5)
    score = trust.snapshot()["node-attacker"]["trust_score"]
    return AttackResult(
        attack="replay_duplicate",
        detected=duplicate_detected,
        rejected=duplicate_detected and consensus.votes >= consensus.quorum,
        trust_penalized=score < 100,
        evidence={
            "unique_nodes": sorted(unique_nodes),
            "votes": consensus.votes,
            "quorum": consensus.quorum,
            "attacker_score": score,
        },
    )


def _quorum_failure_attack() -> AttackResult:
    proofs = [
        _proof("node-a", {"value": 42}),
        _proof("node-b", {"value": 42}),
    ]
    trust = TrustEngine()
    try:
        ProofConsensusEngine().decide(proofs, total_nodes=5)
        rejected = False
    except QuorumNotReached:
        rejected = True
    if rejected:
        trust.record_event("node-offline", INVALID_PROOF)
    score = trust.snapshot()["node-offline"]["trust_score"]
    return AttackResult(
        attack="quorum_failure",
        detected=rejected,
        rejected=rejected,
        trust_penalized=score < 100,
        evidence={"offline_score": score},
    )


def _proof(node_id: str, result: Any) -> Dict[str, Any]:
    return {
        "node": node_id,
        "result": result,
        "hash": hash_result(result),
        "signature": "00",
        "metadata": {"contract_id": "attack.demo", "epoch": 0},
    }


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
