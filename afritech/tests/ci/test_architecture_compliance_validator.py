from __future__ import annotations

import json
from pathlib import Path

from architecture_validator.cli import main, run_checks
from architecture_validator.config import load_config
from architecture_validator.metrics import (
    render_autonomous_metrics,
    render_learning_metrics,
    render_predictive_metrics,
    render_prometheus_metrics,
)
from architecture_validator.predictive.governance import (
    build_autonomous_governance_payload,
    build_predictive_governance_payload,
)
from architecture_validator.remediation.agent import GovernanceAgent
from architecture_validator.remediation.cli import main as remediation_main
from architecture_validator.remediation.engine import AutoFixEngine
from architecture_validator.remediation.knowledge_graph import KnowledgeGraph
from architecture_validator.remediation.learning_engine import LearningEngine
from architecture_validator.remediation.optimizer import Optimizer
from architecture_validator.remediation.self_heal import run_self_healing
from architecture_validator.rules.documentation import check_documentation
from architecture_validator.rules.openapi_diff import diff_openapi_breaking_changes
from architecture_validator.rules.blockchain_verification import check_blockchain_verification
from architecture_validator.scanners.ast_scanner import scan_python_ast
from architecture_validator.scanners.ast_engine.solidity import SolidityASTScanner
from architecture_validator.scanners.ast_engine.typescript import TypeScriptASTScanner


def test_architecture_compliance_validator_passes_current_repository():
    results = run_checks()

    assert results
    assert all(result.passed for result in results), [
        (result.name, result.issues) for result in results if not result.passed
    ]


def test_architecture_compliance_validator_json_cli_output(capsys):
    exit_code = main(["--format", "json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload
    assert all(item["passed"] for item in payload)
    assert {item["name"] for item in payload} >= {
        "Multi-Language AST Validation",
        "Semantic OpenAPI Diff",
        "Blockchain Proof Verification",
        "Replay Integrity",
    }


def test_architecture_compliance_validator_writes_json_artifact(tmp_path):
    output_path = tmp_path / "compliance_report.json"

    exit_code = main(["--format", "json", "--output", str(output_path)])

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload
    assert all(item["passed"] for item in payload)


def test_architecture_compliance_config_loads_lists():
    config = load_config()

    assert "## Architecture Invariants" in config["required_sections"]
    assert "/v1/novaride/ecosystem" in config["api_endpoints"]
    assert "dashboard/src" in config["ui_source_roots"]
    assert "direct_db_write" in config["forbidden_python_call_names"]
    assert "tx.origin" in config["forbidden_solidity_patterns"]
    assert "directPayment(" in config["forbidden_typescript_patterns"]
    assert "replay_verified" in config["required_replay_fragments"]


def test_documentation_rule_reports_missing_sections_and_transcript_content(tmp_path):
    doc_path = tmp_path / "architecture.md"
    doc_path.write_text(
        "# NovaRide\n\n"
        "## Security\n\n"
        "This should not contain docker compose output.\n",
        encoding="utf-8",
    )

    result = check_documentation(
        {
            "docs_path": str(doc_path),
            "required_sections": ["## Architecture Invariants", "## Security"],
            "required_fragments": ["User interfaces SHALL NOT execute business authority."],
            "forbidden_patterns": ["docker compose"],
        }
    )

    assert not result.passed
    assert any("Missing required section" in issue for issue in result.issues)
    assert any("Missing required normative fragment" in issue for issue in result.issues)
    assert any("Forbidden transcript/debug content" in issue for issue in result.issues)


def test_ast_scanner_detects_forbidden_authority_calls(tmp_path):
    module = tmp_path / "service.py"
    module.write_text(
        "def run():\n"
        "    direct_db_write({'ride_id': 'ride-1'})\n"
        "    gateway.bypass_novapower()\n",
        encoding="utf-8",
    )

    issues = scan_python_ast([tmp_path], ["direct_db_write", "bypass_novapower"])

    assert any("Forbidden authority call detected: direct_db_write" in issue for issue in issues)
    assert any("Forbidden authority call detected: bypass_novapower" in issue for issue in issues)


def test_typescript_scanner_detects_forbidden_payment_patterns(tmp_path):
    source = tmp_path / "App.tsx"
    source.write_text("export function pay() { directPayment({ amount: 10 }); }\n", encoding="utf-8")

    issues = TypeScriptASTScanner([tmp_path], ["directPayment("]).scan()

    assert any("TypeScript authority violation: directPayment(" in issue for issue in issues)


def test_solidity_scanner_detects_insecure_patterns(tmp_path):
    source = tmp_path / "Unsafe.sol"
    source.write_text(
        "pragma solidity ^0.8.20;\ncontract Unsafe { function owner() public view returns (address) { return tx.origin; } }\n",
        encoding="utf-8",
    )

    issues = SolidityASTScanner([tmp_path], ["tx.origin"]).scan()

    assert any("Solidity insecure pattern: tx.origin" in issue for issue in issues)


def test_openapi_diff_detects_removed_contract_surface_and_type_changes():
    old = {
        "paths": {
            "/v1/novaride/ecosystem": {"get": {"responses": {"200": {"description": "OK"}}}},
            "/v1/payments/refund": {"post": {"responses": {"200": {"description": "OK"}}}},
        },
        "components": {
            "schemas": {
                "Receipt": {
                    "type": "object",
                    "required": ["receipt_id"],
                    "properties": {
                        "receipt_id": {"type": "string"},
                        "amount": {"type": "number"},
                    },
                }
            }
        },
    }
    new = {
        "paths": {
            "/v1/novaride/ecosystem": {"get": {"responses": {"200": {"description": "OK"}}}},
        },
        "components": {
            "schemas": {
                "Receipt": {
                    "type": "object",
                    "required": [],
                    "properties": {
                        "receipt_id": {"type": "integer"},
                    },
                }
            }
        },
    }

    issues = diff_openapi_breaking_changes(old, new)

    assert "BREAKING: Removed endpoint /v1/payments/refund" in issues
    assert "BREAKING: Removed field Receipt.amount" in issues
    assert "BREAKING: Field Receipt.receipt_id type changed from string to integer" in issues


def test_blockchain_verification_rule_checks_anchor_v2_contract_stack():
    result = check_blockchain_verification(load_config())

    assert result.passed
    assert result.name == "Blockchain Proof Verification"


def test_compliance_prometheus_metrics_exporter_renders_score_and_rules():
    payload = {
        "score": 91,
        "rules_total": 2,
        "rules_passed": 1,
        "rules_failed": 1,
        "status": "fail",
        "mode": "unit_test",
        "report": [
            {"name": "Architecture Invariants", "passed": True, "issues": []},
            {"name": "Semantic OpenAPI Diff", "passed": False, "issues": ["removed endpoint"]},
        ],
    }

    text = render_prometheus_metrics(payload)

    assert "novaride_compliance_score 91" in text
    assert 'novaride_compliance_rule_passed{rule="Architecture Invariants"} 1' in text
    assert 'novaride_compliance_rule_passed{rule="Semantic OpenAPI Diff"} 0' in text
    assert 'novaride_compliance_rule_issues{rule="Semantic OpenAPI Diff"} 1' in text


def test_novaride_compliance_metrics_stack_files_are_deployable():
    prometheus = Path("deploy/novaride/monitoring/prometheus.yml").read_text(encoding="utf-8")
    alerts = Path("deploy/novaride/monitoring/architecture_compliance_rules.yml").read_text(
        encoding="utf-8"
    )
    dashboard = Path("deploy/novaride/monitoring/grafana-dashboard.json").read_text(
        encoding="utf-8"
    )
    runbook = Path("docs/operations/NOVARIDE_COMPLIANCE_METRICS_STACK.md").read_text(
        encoding="utf-8"
    )

    assert "/metrics/architecture/compliance" in prometheus
    assert "novaride_compliance_rules_failed > 0" in alerts
    assert "novaride_compliance_score" in dashboard
    assert "Semantic OpenAPI Diff" in dashboard
    assert "Prometheus-compatible metrics" in runbook


def test_autonomous_remediation_docs_and_ci_are_wired():
    workflow = Path(".github/workflows/architecture.yml").read_text(encoding="utf-8")
    runbook = Path("docs/operations/NOVARIDE_AUTONOMOUS_REMEDIATION.md").read_text(
        encoding="utf-8"
    )
    predictive = Path("docs/operations/NOVARIDE_PREDICTIVE_GOVERNANCE.md").read_text(
        encoding="utf-8"
    )
    autonomous = Path("docs/operations/NOVARIDE_AUTONOMOUS_MULTI_AGENT_GOVERNANCE.md").read_text(
        encoding="utf-8"
    )
    spec = Path("docs/architecture/NOVARIDE_NEXT_GENERATION_ECOSYSTEM.md").read_text(
        encoding="utf-8"
    )
    validator_config = Path("architecture_validator/config.yaml").read_text(encoding="utf-8")

    assert "architecture_validator.remediation.cli" in workflow
    assert "architecture_remediation_report.json" in workflow
    assert "requires human approval for high-risk changes" in runbook
    assert "/v1/architecture/learning" in runbook
    assert "/metrics/architecture/learning" in runbook
    assert "/v1/architecture/predictive-governance" in predictive
    assert "/metrics/architecture/predictive-governance" in predictive
    assert "Autonomous Remediation Rules" in spec
    assert "Continuous Learning Rules" in spec
    assert "Digital Twin Simulation" in spec
    assert "Predictive Governance" in spec
    assert "The digital twin SHALL simulate changes without executing them." in validator_config
    assert "Autonomous Multi-Agent Governance" in spec
    assert "Crisis Simulation" in spec
    assert "Economic Optimization" in spec
    assert "Self-Refactoring Architecture" in spec
    assert "/v1/architecture/autonomous-governance" in autonomous
    assert "/metrics/architecture/autonomous-governance" in autonomous


def test_governance_agent_maps_validator_failures_to_safe_remediation_plan():
    report = [
        {
            "name": "Semantic OpenAPI Diff",
            "passed": False,
            "issues": ["BREAKING: Removed endpoint /v1/payments/refund"],
        },
        {
            "name": "Multi-Language AST Validation",
            "passed": False,
            "issues": ["service.py:12: Forbidden authority call detected: direct_db_write"],
        },
    ]

    fixes = GovernanceAgent(AutoFixEngine()).process(report)

    assert [fix.action for fix in fixes] == [
        "restore_or_version_endpoint",
        "route_through_novapower_policy",
    ]
    assert all(not fix.safe_to_apply for fix in fixes)
    assert all(fix.risk == "high" for fix in fixes)


def test_self_healing_loop_returns_compliant_plan_for_clean_repository():
    payload = run_self_healing()

    assert payload["classification"] == "NOVARIDE_AUTONOMOUS_REMEDIATION_REPORT"
    assert payload["mode"] == "plan"
    assert payload["initial_passed"] is True
    assert payload["final_passed"] is True
    assert payload["fixes_total"] == 0


def test_remediation_cli_writes_report(tmp_path, capsys):
    output_path = tmp_path / "architecture_remediation_report.json"

    exit_code = remediation_main(["--output", str(output_path)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["classification"] == "NOVARIDE_AUTONOMOUS_REMEDIATION_REPORT"
    assert written["final_passed"] is True


def test_learning_engine_records_patterns_and_optimizer_suggestions(tmp_path):
    memory_path = tmp_path / "architecture_learning_memory.json"
    engine = LearningEngine(memory_path)
    engine.record_event(
        "Forbidden authority call detected: direct_db_write",
        {"action": "route_through_novapower_policy"},
        True,
    )
    engine.record_event(
        "Forbidden authority call detected: direct_db_write",
        {"action": "route_through_novapower_policy"},
        False,
    )
    engine.record_event(
        "Forbidden authority call detected: direct_db_write",
        {"action": "route_through_novapower_policy"},
        False,
    )

    patterns = engine.learn_patterns()
    graph = KnowledgeGraph()
    graph.add_edge(
        "Forbidden authority call detected: direct_db_write",
        {"action": "route_through_novapower_policy"},
        True,
    )
    optimizer = Optimizer()
    suggestions = optimizer.analyze(patterns)
    risk_profile = optimizer.risk_profile(patterns)

    assert patterns["Forbidden authority call detected: direct_db_write"]["success"] == 1
    assert patterns["Forbidden authority call detected: direct_db_write"]["fail"] == 2
    assert graph.get_best_fix("Forbidden authority call detected: direct_db_write") == {
        "action": "route_through_novapower_policy"
    }
    assert "Improve rule or fix strategy for: Forbidden authority call detected: direct_db_write" in suggestions
    assert risk_profile["risk"] == "high"
    assert risk_profile["total"] == 3


def test_learning_metrics_renderer_exports_learning_gauges():
    payload = {
        "learning": {
            "patterns": {
                "Forbidden authority call detected: direct_db_write": {"success": 3, "fail": 1}
            },
            "risk_profile": {
                "risk": "low",
                "score": 75,
                "total": 4,
                "success": 3,
                "fail": 1,
            },
            "optimizer_suggestions": ["Promote stable remediation pattern for: direct_db_write"],
        }
    }

    text = render_learning_metrics(payload)

    assert "novaride_ai_fix_accuracy 75" in text
    assert "novaride_architecture_violation_rate 25" in text
    assert "novaride_learning_total_events 4" in text
    assert "novaride_learning_suggestions_total 1" in text
    assert 'novaride_learning_issue_success_rate{issue="Forbidden authority call detected: direct_db_write"} 75' in text
    assert 'novaride_learning_issue_fail_total{issue="Forbidden authority call detected: direct_db_write"} 1' in text


def test_predictive_governance_payload_and_metrics_are_available():
    payload = build_predictive_governance_payload(live=False)
    text = render_predictive_metrics(payload)

    assert payload["classification"] == "NOVARIDE_PREDICTIVE_GOVERNANCE_REPORT"
    assert payload["authority_boundary"] == "predictive_governance_is_advisory_and_simulation_only"
    assert payload["digital_twin"]["scenario_count"] == 4
    assert payload["predictions"]
    assert payload["preventive_actions"]
    assert payload["risk_score"] >= 0
    assert "novaride_predictive_risk_score" in text
    assert "novaride_digital_twin_health_score" in text
    assert "novaride_predicted_risks_total" in text
    assert "novaride_preventive_actions_total" in text


def test_autonomous_governance_payload_and_metrics_are_available():
    payload = build_autonomous_governance_payload(live=False)
    text = render_autonomous_metrics(payload)

    assert payload["classification"] == "NOVARIDE_AUTONOMOUS_MULTI_AGENT_GOVERNANCE_REPORT"
    assert payload["authority_boundary"] == "multi_agent_governance_is_advisory_and_simulation_only"
    assert payload["multi_agent"]["agent_count"] >= 1
    assert payload["crisis_summary"]["scenario_count"] == 6
    assert payload["crisis_summary"]["black_swan"]["impact"] == "CRITICAL"
    assert payload["economic_optimization"]["authority_boundary"] == "advisory_only"
    assert payload["refactor_suggestions"]
    assert "novaride_multi_agent_findings_total" in text
    assert "novaride_crisis_max_risk_score" in text
    assert "novaride_crisis_critical_scenarios_total" in text
    assert "novaride_economic_efficiency" in text
    assert "novaride_refactor_suggestions_total" in text


def test_self_healing_loop_records_learning_history(tmp_path):
    memory_path = tmp_path / "architecture_learning_memory.json"
    artifact_path = tmp_path / "architecture_remediation_report.json"

    payload = run_self_healing(
        apply=True,
        allow_risky=False,
        artifact_path=artifact_path,
        learning_memory_path=memory_path,
    )

    assert payload["classification"] == "NOVARIDE_AUTONOMOUS_REMEDIATION_REPORT"
    assert payload["learning"]["memory_path"] == str(memory_path)
    assert "risk_profile" in payload["learning"]
    assert "patterns" in payload["learning"]
