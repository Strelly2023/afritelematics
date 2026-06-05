from __future__ import annotations

import json
from typing import Dict


class ObservabilityExporter:
    def to_json(self, snapshot: Dict[str, object]) -> str:
        return json.dumps(snapshot, sort_keys=True, default=str)

    def to_prometheus(self, snapshot: Dict[str, object]) -> str:
        lines = []
        for key, value in sorted(snapshot.items()):
            if isinstance(value, (int, float)):
                metric = key.replace("-", "_").replace(".", "_")
                lines.append(f"afritech_{metric} {value}")
        return "\n".join(lines)

    def export_chain(self, ledger) -> list[Dict[str, object]]:
        blocks = getattr(ledger, "_blocks", None)
        if blocks is None and hasattr(ledger, "get_blocks"):
            return [
                {
                    "index": block.get("index"),
                    "hash": block.get("hash"),
                    "prev": block.get("prev_hash"),
                    "proofs": len(block.get("proofs", [])),
                }
                for block in ledger.get_blocks()
            ]

        return [
            {
                "index": block.index,
                "hash": block.hash,
                "prev": block.prev_hash,
                "proofs": len(block.proofs),
            }
            for block in blocks or []
        ]

    def export_proofs(self, blocks) -> list[object]:
        return [
            block.get("proofs", []) if isinstance(block, dict) else getattr(block, "proofs", [])
            for block in blocks
        ]

    def export_state(self, state: Dict[str, object]) -> Dict[str, object]:
        return dict(state)

    def export_metrics(self, metrics: Dict[str, object]) -> Dict[str, object]:
        return dict(metrics)


def export_chain(ledger) -> list[Dict[str, object]]:
    return ObservabilityExporter().export_chain(ledger)


def export_proofs(blocks) -> list[object]:
    return ObservabilityExporter().export_proofs(blocks)


def export_state(state: Dict[str, object]) -> Dict[str, object]:
    return ObservabilityExporter().export_state(state)


def export_metrics(metrics: Dict[str, object]) -> Dict[str, object]:
    return ObservabilityExporter().export_metrics(metrics)
