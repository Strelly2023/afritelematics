from __future__ import annotations

from afritech.distributed.state.state_machine import LedgerStateMachine
from afritech.distributed.testing.afriride_ledger_scenario import (
    run_afriride_ledger_scenario,
)
from afritech.distributed.testing.sovereign_ledger_protocol import (
    run_five_node_validation,
    run_malicious_node_validation,
)
from afritech.runtime.audit.ledger import AuditLedger


def test_five_node_validation_commits_consensus_block():
    result = run_five_node_validation()

    assert result["chain_valid"] is True
    assert result["consensus"]["votes"] == 5
    assert result["block"]["prev_hash"] == "GENESIS"
    assert len(result["block"]["proofs"]) == 5
    assert len(result["state"]["executions"]) == 1


def test_malicious_node_is_excluded_and_penalized():
    result = run_malicious_node_validation()

    assert result["chain_valid"] is True
    assert "node-malicious" not in result["accepted_nodes"]
    assert result["trust"]["node-malicious"]["trust_score"] < 100
    assert result["trust"]["node-tampered"]["trust_score"] < 100


def test_ledger_state_machine_replays_committed_blocks():
    ledger = AuditLedger()
    ledger.commit_block(
        [
            {
                "node": "node-a",
                "result": {"value": 1},
                "hash": "hash-a",
                "signature": "00",
                "metadata": {"contract_id": "contract.demo"},
            }
        ]
    )

    state = LedgerStateMachine().replay_ledger(ledger)

    assert state["executions"][0]["node"] == "node-a"
    assert state["executions"][0]["contract_id"] == "contract.demo"
    assert state["executions"][0]["block_index"] == 0


def test_afriride_ledger_scenario_projects_completed_ride_state():
    result = run_afriride_ledger_scenario()

    assert result["chain_valid"] is True
    assert len(result["blocks"]) == 3
    ride = result["state"]["rides"]["ride-001"]
    assert ride["status"] == "completed"
    assert ride["driver_id"] == "driver-001"
    assert result["state"]["receipts"]["receipt-ride-001"]["fare"] > 0
