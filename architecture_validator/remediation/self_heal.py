from __future__ import annotations

from pathlib import Path
from typing import Any

from architecture_validator.cli import run_checks
from architecture_validator.config import DEFAULT_CONFIG_PATH
from architecture_validator.remediation.agent import GovernanceAgent
from architecture_validator.remediation.executor import FixExecutor
from architecture_validator.remediation.knowledge_graph import KnowledgeGraph
from architecture_validator.remediation.learning_engine import LearningEngine
from architecture_validator.remediation.optimizer import Optimizer


def run_self_healing(
    *,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    apply: bool = False,
    allow_risky: bool = False,
    artifact_path: str | Path = "architecture_remediation_report.json",
    learning_memory_path: str | Path = "architecture_learning_memory.json",
) -> dict[str, Any]:
    initial_results = run_checks(config_path)
    initial_report = [result.as_dict() for result in initial_results]
    fixes = GovernanceAgent().process(initial_report)
    executions = FixExecutor(artifact_path).execute(
        fixes,
        apply=apply,
        allow_risky=allow_risky,
    )
    final_results = run_checks(config_path)
    final_report = [result.as_dict() for result in final_results]
    learning = LearningEngine(learning_memory_path)
    knowledge_graph = KnowledgeGraph()
    for event in learning.memory:
        fix_payload = event.get("fix") if isinstance(event, dict) else None
        if not isinstance(event, dict) or not isinstance(fix_payload, dict):
            continue
        knowledge_graph.add_edge(str(event.get("issue") or "unknown"), fix_payload, bool(event.get("success")))
    final_passed = all(result.passed for result in final_results)
    if apply:
        for fix in fixes:
            success = final_passed and (fix.safe_to_apply or allow_risky)
            learning.record_event(fix.issue, fix, success)
            knowledge_graph.add_edge(fix.issue, fix, success)
    patterns = learning.learn_patterns()
    optimizer = Optimizer()
    return {
        "classification": "NOVARIDE_AUTONOMOUS_REMEDIATION_REPORT",
        "mode": "apply" if apply else "plan",
        "allow_risky": allow_risky,
        "initial_passed": all(result.passed for result in initial_results),
        "final_passed": final_passed,
        "fixes_total": len(fixes),
        "manual_review_required": sum(
            1 for result in executions if result.status == "manual_review_required"
        ),
        "fixes": [fix.as_dict() for fix in fixes],
        "executions": [result.as_dict() for result in executions],
        "initial_report": initial_report,
        "final_report": final_report,
        "learning": {
            "memory_path": str(Path(learning_memory_path)),
            "patterns": patterns,
            "knowledge_graph": knowledge_graph.summarize(),
            "optimizer_suggestions": optimizer.analyze(patterns),
            "risk_profile": optimizer.risk_profile(patterns),
        },
    }
