from __future__ import annotations

from typing import Any, Dict, List


def inspect_ledger(ledger) -> List[Dict[str, Any]]:
    if not hasattr(ledger, "get_blocks"):
        raise TypeError("ledger must expose get_blocks()")
    return [
        {
            "index": block["index"],
            "hash": block["hash"],
            "prev_hash": block["prev_hash"],
            "proof_count": len(block.get("proofs", [])),
        }
        for block in ledger.get_blocks()
    ]


def inspect_state(state_service) -> Dict[str, Any]:
    if not hasattr(state_service, "snapshot"):
        raise TypeError("state_service must expose snapshot()")
    return state_service.snapshot()
