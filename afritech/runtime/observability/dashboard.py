from __future__ import annotations

from typing import Dict


class ObservabilityDashboard:
    def render(self, snapshot: Dict[str, object]) -> Dict[str, object]:
        metrics = snapshot.get("metrics", {})
        traces = snapshot.get("traces", {})
        trust = snapshot.get("trust", {})
        return {
            "status": "ok",
            "metric_sections": len(metrics) if isinstance(metrics, dict) else 0,
            "trace_sections": len(traces) if isinstance(traces, dict) else 0,
            "trust_nodes": len(trust) if isinstance(trust, dict) else 0,
            "snapshot": snapshot,
        }


def show_dashboard(ledger, state_service) -> Dict[str, object]:
    blocks = ledger.get_blocks() if hasattr(ledger, "get_blocks") else []
    state = state_service.snapshot() if hasattr(state_service, "snapshot") else {}
    return {
        "blocks": len(blocks),
        "rides": state.get("rides", {}),
        "receipts": state.get("receipts", {}),
        "executions": state.get("executions", []),
    }
