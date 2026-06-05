from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict

from afritech.distributed.testing.afriride_ledger_scenario import (
    run_afriride_ledger_scenario,
)
from afritech.distributed.testing.hardening_suite import (
    run_system_integration_hardening_suite,
)
from afritech.distributed.testing.protocol_scenarios import (
    run_multi_scenario_protocol_validation,
)


PILOT_DOC = Path("docs/pilot/AFRIRIDE_MULTI_NODE_PRODUCTION_PILOT_PREP.md")


async def build_afriride_multi_node_pilot_readiness() -> Dict[str, Any]:
    hardening = await run_system_integration_hardening_suite()
    scenarios = run_multi_scenario_protocol_validation()
    afriride = run_afriride_ledger_scenario()

    live_gates = {
        "render_health_200": False,
        "events_endpoint_live": False,
        "real_devices_installed": False,
        "operator_observing_live": False,
        "replay_export_live": False,
    }

    payload = {
        "schema": "afriride.multi_node.production_pilot_readiness.v1",
        "classification": "pilot_prepared_live_execution_hold",
        "pilot_run_id": "live_pilot_001",
        "prep_doc": str(PILOT_DOC),
        "repo_side_ready": (
            hardening["passed"]
            and scenarios["passed"]
            and afriride["chain_valid"]
        ),
        "live_gates": live_gates,
        "go_authorized": all(live_gates.values()),
        "hardening": hardening,
        "multi_scenario_validation": scenarios,
        "afriride_simulation": {
            "chain_valid": afriride["chain_valid"],
            "block_count": len(afriride["blocks"]),
            "state": afriride["state"],
        },
    }
    payload["readiness_hash"] = _canonical_hash(payload)
    return payload


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
