from __future__ import annotations

import asyncio
from typing import Dict

from afritech.distributed.testing.production_pilot_prep import (
    build_afriride_multi_node_pilot_readiness,
)


def run() -> Dict[str, object]:
    report = asyncio.run(build_afriride_multi_node_pilot_readiness())
    return {
        "command": "run-pilot-check",
        "status": "hold" if not report["go_authorized"] else "authorized",
        "summary": (
            "AfriRide pilot check: "
            f"{'AUTHORIZED' if report['go_authorized'] else 'HOLD'}"
        ),
        "report": report,
    }
