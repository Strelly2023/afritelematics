from __future__ import annotations

from pathlib import Path

from afritech.cli.main import main
from afritech.distributed.services.state_service import StateService
from afritech.distributed.testing.afriride_ledger_scenario import (
    run_afriride_ledger_scenario,
)
from afritech.runtime.audit.ledger import AuditLedger
from afritech.runtime.observability.dashboard import show_dashboard
from afritech.runtime.observability.exporter import (
    export_chain,
    export_metrics,
    export_proofs,
    export_state,
)
from afritech.tools.inspector import inspect_ledger, inspect_state
from afritech.tools.test_runner import run_all_tests


REQUIRED_DOCS = [
    "docs/README.md",
    "docs/architecture/system_overview.md",
    "docs/protocol/protocol_definition.md",
    "docs/network/network.md",
    "docs/execution/execution_model.md",
    "docs/consensus/consensus.md",
    "docs/trust/trust_model.md",
    "docs/ledger/ledger.md",
    "docs/state/state_machine.md",
    "docs/observability/observability.md",
    "docs/testing/testing.md",
    "docs/pilot/pilot_architecture.md",
    "docs/developer/getting_started.md",
    "docs/api/state_service_api.md",
]


def test_required_documentation_files_exist():
    for path in REQUIRED_DOCS:
        assert Path(path).exists(), path


def test_cli_commands_execute():
    assert main(["inspect-chain"]) == 0
    assert main(["simulate-5-node"]) == 0
    assert main(["simulate-20-node"]) == 0
    assert main(["simulate-network"]) == 0
    assert main(["run-pilot-check"]) == 0
    assert main(["start-node"]) == 0


def test_tool_runner_executes_protocol_suites():
    report = run_all_tests()

    assert report["passed"] is True


def test_inspector_exporter_and_dashboard_helpers():
    scenario = run_afriride_ledger_scenario()
    ledger = AuditLedger()
    for block in scenario["blocks"]:
        ledger.commit_block(block["proofs"])

    service = StateService()
    service.load_state(scenario["state"])

    assert inspect_ledger(ledger)
    assert inspect_state(service)["rides"]["ride-001"]["status"] == "completed"
    assert export_chain(ledger)
    assert export_proofs(ledger.get_blocks())
    assert export_state(service.snapshot())["rides"]
    assert export_metrics({"nodes": 1})["nodes"] == 1
    assert show_dashboard(ledger, service)["blocks"] == 3
