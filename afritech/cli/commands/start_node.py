from __future__ import annotations

from typing import Dict


def run() -> Dict[str, object]:
    return {
        "command": "start-node",
        "status": "prepared",
        "summary": "Node start is prepared. Use run_node.py for an interactive node process.",
    }
