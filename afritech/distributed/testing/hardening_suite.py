from __future__ import annotations

import asyncio
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Dict, List

from afritech.distributed.consensus.consensus_engine import ProofConsensusEngine
from afritech.distributed.proof import hash_result
from afritech.runtime.audit.ledger import AuditLedger


@dataclass(frozen=True)
class HardeningScenarioResult:
    scenario: str
    passed: bool
    evidence: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario": self.scenario,
            "passed": self.passed,
            "evidence": self.evidence,
        }


async def run_async_execution_stress(
    executions: int = 32,
    node_count: int = 5,
) -> HardeningScenarioResult:
    ledger = AuditLedger()
    consensus = ProofConsensusEngine()

    async def execute(index: int) -> str:
        await asyncio.sleep(0)
        result = {"execution": index, "value": index * 2}
        proofs = _proofs(
            nodes=[f"node-{n}" for n in range(node_count)],
            result=result,
            contract_id="stress.double",
        )
        accepted = consensus.decide(proofs, total_nodes=node_count)
        block = ledger.commit_block(accepted.proofs)
        return block.hash

    hashes = await asyncio.gather(*(execute(index) for index in range(executions)))

    return HardeningScenarioResult(
        scenario="async_execution_stress",
        passed=len(hashes) == executions and ledger.verify_chain(),
        evidence={
            "executions": executions,
            "node_count": node_count,
            "block_count": len(ledger.get_blocks()),
            "chain_valid": ledger.verify_chain(),
            "terminal_block_hash": hashes[-1] if hashes else "",
        },
    )


def run_network_instability_simulation() -> HardeningScenarioResult:
    nodes = ["node-a", "node-b", "node-c", "node-d", "node-e"]
    delivered_nodes = ["node-a", "node-c", "node-e"]
    result = {"route": "network.instability", "value": 17}
    proofs = _proofs(delivered_nodes, result, "network.instability")

    consensus = ProofConsensusEngine().decide(proofs, total_nodes=len(nodes))
    ledger = AuditLedger()
    block = ledger.commit_block(consensus.proofs)

    return HardeningScenarioResult(
        scenario="network_instability",
        passed=consensus.votes == 3 and ledger.verify_chain(),
        evidence={
            "available_nodes": nodes,
            "delivered_nodes": delivered_nodes,
            "dropped_nodes": sorted(set(nodes) - set(delivered_nodes)),
            "votes": consensus.votes,
            "quorum": consensus.quorum,
            "block_hash": block.hash,
        },
    )


def run_partial_node_failure_simulation() -> HardeningScenarioResult:
    nodes = ["node-a", "node-b", "node-c", "node-d", "node-e"]
    failed_nodes = ["node-d", "node-e"]
    active_nodes = [node for node in nodes if node not in failed_nodes]
    result = {"route": "partial.failure", "value": 23}
    proofs = _proofs(active_nodes, result, "partial.failure")

    consensus = ProofConsensusEngine().decide(proofs, total_nodes=len(nodes))
    ledger = AuditLedger()
    block = ledger.commit_block(consensus.proofs)

    return HardeningScenarioResult(
        scenario="partial_node_failure",
        passed=ledger.verify_chain() and consensus.votes == len(active_nodes),
        evidence={
            "active_nodes": active_nodes,
            "failed_nodes": failed_nodes,
            "votes": consensus.votes,
            "quorum": consensus.quorum,
            "block_hash": block.hash,
        },
    )


async def run_system_integration_hardening_suite() -> Dict[str, Any]:
    scenarios = [
        await run_async_execution_stress(),
        run_network_instability_simulation(),
        run_partial_node_failure_simulation(),
    ]
    payload = {
        "schema": "afritech.system_integration_hardening.v1",
        "passed": all(scenario.passed for scenario in scenarios),
        "scenarios": [scenario.to_dict() for scenario in scenarios],
    }
    payload["evidence_hash"] = _canonical_hash(payload)
    return payload


def _proofs(nodes: List[str], result: Any, contract_id: str) -> List[Dict[str, Any]]:
    return [
        {
            "node": node,
            "result": result,
            "hash": hash_result(result),
            "signature": "00",
            "metadata": {"contract_id": contract_id, "epoch": 0},
        }
        for node in nodes
    ]


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
