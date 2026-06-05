from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Dict, Iterable, List

from afritech.distributed.consensus.consensus_engine import ProofConsensusEngine
from afritech.distributed.proof import hash_result
from afritech.distributed.state.state_machine import LedgerStateMachine
from afritech.runtime.audit.ledger import AuditLedger


NODES = ["node-a", "node-b", "node-c", "node-d", "node-e"]


def run_logistics_scenario() -> Dict[str, Any]:
    events = [
        ("logistics.pickup", {"shipment_id": "ship-001", "status": "picked_up"}),
        ("logistics.sort", {"shipment_id": "ship-001", "hub": "hub-01"}),
        ("logistics.deliver", {"shipment_id": "ship-001", "status": "delivered"}),
    ]
    return _run_scenario("logistics", events, _logistics_reducer)


def run_finance_scenario() -> Dict[str, Any]:
    events = [
        ("finance.debit", {"account": "acct-a", "amount": 25}),
        ("finance.credit", {"account": "acct-b", "amount": 25}),
        ("finance.settle", {"settlement_id": "settle-001", "status": "settled"}),
    ]
    return _run_scenario(
        "finance",
        events,
        _finance_reducer,
        initial_state={"balances": {"acct-a": 100, "acct-b": 10}},
    )


def run_supply_chain_scenario() -> Dict[str, Any]:
    events = [
        ("supply_chain.manufacture", {"lot_id": "lot-001", "status": "manufactured"}),
        ("supply_chain.inspect", {"lot_id": "lot-001", "quality": "passed"}),
        ("supply_chain.release", {"lot_id": "lot-001", "status": "released"}),
    ]
    return _run_scenario("supply_chain", events, _supply_chain_reducer)


def run_multi_scenario_protocol_validation() -> Dict[str, Any]:
    scenarios = [
        run_logistics_scenario(),
        run_finance_scenario(),
        run_supply_chain_scenario(),
    ]
    payload = {
        "schema": "afritech.multi_scenario_protocol_validation.v1",
        "passed": all(scenario["chain_valid"] for scenario in scenarios),
        "scenarios": scenarios,
    }
    payload["evidence_hash"] = _canonical_hash(payload)
    return payload


def _run_scenario(
    name: str,
    events: Iterable[tuple[str, Dict[str, Any]]],
    reducer,
    initial_state: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    consensus = ProofConsensusEngine()
    ledger = AuditLedger()

    contracts = set()
    for contract_id, result in events:
        contracts.add(contract_id)
        proofs = _proofs(result, contract_id)
        accepted = consensus.decide(proofs, total_nodes=len(NODES))
        ledger.commit_block(accepted.proofs)

    state_machine = LedgerStateMachine()
    for contract_id in contracts:
        state_machine.register_reducer(contract_id, reducer)

    state = state_machine.replay_ledger(ledger, initial_state)
    return {
        "scenario": name,
        "chain_valid": ledger.verify_chain(),
        "block_count": len(ledger.get_blocks()),
        "terminal_hash": ledger.get_blocks()[-1]["hash"],
        "state": state,
    }


def _proofs(result: Dict[str, Any], contract_id: str) -> List[Dict[str, Any]]:
    return [
        {
            "node": node,
            "result": result,
            "hash": hash_result(result),
            "signature": "00",
            "metadata": {"contract_id": contract_id, "epoch": 0},
        }
        for node in NODES
    ]


def _logistics_reducer(state: Dict[str, Any], proof: Dict[str, Any]) -> Dict[str, Any]:
    result = proof["result"]
    shipments = state.setdefault("shipments", {})
    shipment = shipments.setdefault(result["shipment_id"], {"shipment_id": result["shipment_id"]})
    shipment.update(result)
    return state


def _finance_reducer(state: Dict[str, Any], proof: Dict[str, Any]) -> Dict[str, Any]:
    result = proof["result"]
    balances = state.setdefault("balances", {})
    contract_id = proof["metadata"]["contract_id"]
    if contract_id == "finance.debit":
        balances[result["account"]] = balances.get(result["account"], 0) - result["amount"]
    elif contract_id == "finance.credit":
        balances[result["account"]] = balances.get(result["account"], 0) + result["amount"]
    else:
        state["settlement"] = dict(result)
    return state


def _supply_chain_reducer(state: Dict[str, Any], proof: Dict[str, Any]) -> Dict[str, Any]:
    result = proof["result"]
    lots = state.setdefault("lots", {})
    lot = lots.setdefault(result["lot_id"], {"lot_id": result["lot_id"]})
    lot.update(result)
    return state


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
