from __future__ import annotations

from typing import Any, Dict, List

from afritech.distributed.consensus.consensus_engine import ProofConsensusEngine
from afritech.distributed.proof import hash_result
from afritech.distributed.state.state_machine import LedgerStateMachine
from afritech.runtime.audit.ledger import AuditLedger


PILOT_RUN_ID = "live_pilot_001"


def ride_pricing_contract(distance_km: float, base_fare: float = 3.0) -> Dict[str, Any]:
    fare = round(base_fare + (distance_km * 1.8), 2)
    return {
        "fare": fare,
        "currency": "USD",
        "distance_km": distance_km,
    }


def ride_match_contract(ride_id: str, driver_id: str, rider_id: str) -> Dict[str, Any]:
    return {
        "ride_id": ride_id,
        "driver_id": driver_id,
        "rider_id": rider_id,
        "status": "matched",
    }


def trip_complete_contract(ride_id: str, fare: float) -> Dict[str, Any]:
    return {
        "ride_id": ride_id,
        "fare": fare,
        "status": "completed",
        "receipt_id": f"receipt-{ride_id}",
    }


def _proof_batch(
    contract_id: str,
    result: Dict[str, Any],
    nodes: List[str],
) -> List[Dict[str, Any]]:
    return [
        {
            "node": node_id,
            "result": result,
            "hash": hash_result(result),
            "signature": "00",
            "metadata": {
                "contract_id": contract_id,
                "epoch": 0,
                "pilot_run_id": PILOT_RUN_ID,
            },
        }
        for node_id in nodes
    ]


def _afriride_reducer(state: Dict[str, Any], proof: Dict[str, Any]) -> Dict[str, Any]:
    result = proof.get("result", {})
    metadata = proof.get("metadata", {})
    contract_id = metadata.get("contract_id")

    rides = state.setdefault("rides", {})
    receipts = state.setdefault("receipts", {})

    if contract_id == "afriride.ride_match" and isinstance(result, dict):
        rides[result["ride_id"]] = {
            "ride_id": result["ride_id"],
            "driver_id": result["driver_id"],
            "rider_id": result["rider_id"],
            "status": result["status"],
        }

    if contract_id == "afriride.trip_complete" and isinstance(result, dict):
        ride = rides.setdefault(result["ride_id"], {"ride_id": result["ride_id"]})
        ride["status"] = result["status"]
        ride["fare"] = result["fare"]
        receipts[result["receipt_id"]] = dict(result)

    return state


def run_afriride_ledger_scenario() -> Dict[str, Any]:
    nodes = ["node-a", "node-b", "node-c", "node-d", "node-e"]
    consensus_engine = ProofConsensusEngine()
    ledger = AuditLedger()

    match_result = ride_match_contract(
        ride_id="ride-001",
        driver_id="driver-001",
        rider_id="rider-001",
    )
    pricing_result = ride_pricing_contract(distance_km=4.2)
    complete_result = trip_complete_contract(
        ride_id="ride-001",
        fare=pricing_result["fare"],
    )

    for contract_id, result in (
        ("afriride.ride_match", match_result),
        ("afriride.pricing", pricing_result),
        ("afriride.trip_complete", complete_result),
    ):
        proofs = _proof_batch(contract_id, result, nodes)
        consensus = consensus_engine.decide(proofs, total_nodes=len(nodes))
        ledger.commit_block(consensus.proofs)

    state_machine = LedgerStateMachine()
    state_machine.register_reducer("afriride.ride_match", _afriride_reducer)
    state_machine.register_reducer("afriride.trip_complete", _afriride_reducer)
    state = state_machine.replay_ledger(ledger)

    return {
        "pilot_run_id": PILOT_RUN_ID,
        "chain_valid": ledger.verify_chain(),
        "blocks": ledger.get_blocks(),
        "state": state,
    }
