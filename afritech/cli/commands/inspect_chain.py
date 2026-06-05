from __future__ import annotations

from typing import Dict

from afritech.distributed.testing.afriride_ledger_scenario import (
    run_afriride_ledger_scenario,
)


def run() -> Dict[str, object]:
    scenario = run_afriride_ledger_scenario()
    blocks = scenario["blocks"]
    return {
        "command": "inspect-chain",
        "status": "passed" if scenario["chain_valid"] else "failed",
        "summary": f"AfriRide simulated chain blocks: {len(blocks)}",
        "chain_valid": scenario["chain_valid"],
        "blocks": [
            {
                "index": block["index"],
                "hash": block["hash"],
                "prev_hash": block["prev_hash"],
                "proof_count": len(block["proofs"]),
            }
            for block in blocks
        ],
    }
