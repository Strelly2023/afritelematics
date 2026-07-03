from __future__ import annotations

from typing import Any


def render_prometheus_metrics(payload: dict[str, Any]) -> str:
    """Render architecture compliance payload as Prometheus exposition text."""

    report = payload.get("report") if isinstance(payload.get("report"), list) else []
    lines = [
        "# HELP novaride_compliance_score Current architecture compliance score.",
        "# TYPE novaride_compliance_score gauge",
        f"novaride_compliance_score {float(payload.get('score') or 0):.0f}",
        "# HELP novaride_compliance_rules_total Total architecture compliance rules evaluated.",
        "# TYPE novaride_compliance_rules_total gauge",
        f"novaride_compliance_rules_total {int(payload.get('rules_total') or len(report))}",
        "# HELP novaride_compliance_rules_passed Architecture compliance rules currently passing.",
        "# TYPE novaride_compliance_rules_passed gauge",
        f"novaride_compliance_rules_passed {int(payload.get('rules_passed') or 0)}",
        "# HELP novaride_compliance_rules_failed Architecture compliance rules currently failing.",
        "# TYPE novaride_compliance_rules_failed gauge",
        f"novaride_compliance_rules_failed {int(payload.get('rules_failed') or 0)}",
        "# HELP novaride_compliance_rule_passed Per-rule pass status, 1 for pass and 0 for fail.",
        "# TYPE novaride_compliance_rule_passed gauge",
    ]

    for rule in report:
        if not isinstance(rule, dict):
            continue
        name = _label(str(rule.get("name") or "unknown"))
        passed = 1 if rule.get("passed") is True else 0
        issues = rule.get("issues") if isinstance(rule.get("issues"), list) else []
        lines.append(f'novaride_compliance_rule_passed{{rule="{name}"}} {passed}')
        lines.append(f'novaride_compliance_rule_issues{{rule="{name}"}} {len(issues)}')

    mode = _label(str(payload.get("mode") or "unknown"))
    status = _label(str(payload.get("status") or "unknown"))
    lines.extend(
        [
            "# HELP novaride_compliance_report_info Compliance report metadata.",
            "# TYPE novaride_compliance_report_info gauge",
            f'novaride_compliance_report_info{{mode="{mode}",status="{status}"}} 1',
        ]
    )
    return "\n".join(lines) + "\n"


def render_learning_metrics(payload: dict[str, Any]) -> str:
    """Render remediation learning payload as Prometheus exposition text."""

    learning = payload.get("learning") if isinstance(payload.get("learning"), dict) else {}
    if not learning:
        learning = payload if isinstance(payload, dict) else {}
    patterns = learning.get("patterns") if isinstance(learning.get("patterns"), dict) else {}
    risk_profile = (
        learning.get("risk_profile") if isinstance(learning.get("risk_profile"), dict) else {}
    )
    suggestions = (
        learning.get("optimizer_suggestions")
        if isinstance(learning.get("optimizer_suggestions"), list)
        else []
    )
    total_success = int(risk_profile.get("success") or 0)
    total_fail = int(risk_profile.get("fail") or 0)
    total = int(risk_profile.get("total") or (total_success + total_fail))
    accuracy = int(risk_profile.get("score") or 0)
    violation_rate = int(round((total_fail / total) * 100)) if total else 0
    lines = [
        "# HELP novaride_ai_fix_accuracy Auto-fix success rate learned from remediation outcomes.",
        "# TYPE novaride_ai_fix_accuracy gauge",
        f"novaride_ai_fix_accuracy {accuracy}",
        "# HELP novaride_architecture_violation_rate Violations per learned remediation outcome.",
        "# TYPE novaride_architecture_violation_rate gauge",
        f"novaride_architecture_violation_rate {violation_rate}",
        "# HELP novaride_learning_total_events Total learned remediation events.",
        "# TYPE novaride_learning_total_events gauge",
        f"novaride_learning_total_events {total}",
        "# HELP novaride_learning_suggestions_total Total optimization suggestions emitted.",
        "# TYPE novaride_learning_suggestions_total gauge",
        f"novaride_learning_suggestions_total {len(suggestions)}",
        "# HELP novaride_learning_issue_success_rate Per-issue success rate learned from memory.",
        "# TYPE novaride_learning_issue_success_rate gauge",
    ]
    for issue, stats in patterns.items():
        if not isinstance(stats, dict):
            continue
        issue_label = _label(str(issue))
        success = int(stats.get("success") or 0)
        fail = int(stats.get("fail") or 0)
        denom = success + fail
        issue_score = int(round((success / denom) * 100)) if denom else 0
        lines.append(f'novaride_learning_issue_success_rate{{issue="{issue_label}"}} {issue_score}')
        lines.append(f'novaride_learning_issue_fail_total{{issue="{issue_label}"}} {fail}')
    return "\n".join(lines) + "\n"


def render_predictive_metrics(payload: dict[str, Any]) -> str:
    """Render predictive governance payload as Prometheus exposition text."""

    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
    digital_twin = (
        payload.get("digital_twin") if isinstance(payload.get("digital_twin"), dict) else {}
    )
    predictions = payload.get("predictions") if isinstance(payload.get("predictions"), list) else []
    preventive_actions = (
        payload.get("preventive_actions")
        if isinstance(payload.get("preventive_actions"), list)
        else []
    )
    risk_score = int(payload.get("risk_score") or metrics.get("risk_score") or 0)
    twin_health_score = int(
        digital_twin.get("twin_health_score")
        or metrics.get("twin_health_score")
        or 0
    )
    lines = [
        "# HELP novaride_predictive_risk_score Predictive governance risk score.",
        "# TYPE novaride_predictive_risk_score gauge",
        f"novaride_predictive_risk_score {risk_score}",
        "# HELP novaride_digital_twin_health_score Digital twin health score.",
        "# TYPE novaride_digital_twin_health_score gauge",
        f"novaride_digital_twin_health_score {twin_health_score}",
        "# HELP novaride_predicted_risks_total Total predicted risks across simulated scenarios.",
        "# TYPE novaride_predicted_risks_total gauge",
        f"novaride_predicted_risks_total {int(payload.get('predicted_risks') or metrics.get('predicted_risks') or 0)}",
        "# HELP novaride_prevented_violations_total Total preventive actions recommended.",
        "# TYPE novaride_prevented_violations_total gauge",
        f"novaride_prevented_violations_total {int(payload.get('prevented_violations') or metrics.get('prevented_violations') or 0)}",
        "# HELP novaride_predictive_scenarios_total Total simulated predictive scenarios.",
        "# TYPE novaride_predictive_scenarios_total gauge",
        f"novaride_predictive_scenarios_total {len(payload.get('scenarios') or [])}",
        "# HELP novaride_predictive_predictions_total Total predicted outcomes.",
        "# TYPE novaride_predictive_predictions_total gauge",
        f"novaride_predictive_predictions_total {len(predictions)}",
        "# HELP novaride_preventive_actions_total Total preventive actions recommended.",
        "# TYPE novaride_preventive_actions_total gauge",
        f"novaride_preventive_actions_total {len(preventive_actions)}",
    ]
    return "\n".join(lines) + "\n"


def render_autonomous_metrics(payload: dict[str, Any]) -> str:
    """Render autonomous multi-agent governance payload as Prometheus exposition text."""

    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
    multi_agent = (
        payload.get("multi_agent") if isinstance(payload.get("multi_agent"), dict) else {}
    )
    crisis_summary = (
        payload.get("crisis_summary") if isinstance(payload.get("crisis_summary"), dict) else {}
    )
    economic = (
        payload.get("economic_optimization")
        if isinstance(payload.get("economic_optimization"), dict)
        else {}
    )
    refactors = (
        payload.get("refactor_suggestions")
        if isinstance(payload.get("refactor_suggestions"), list)
        else []
    )
    lines = [
        "# HELP novaride_multi_agent_findings_total Total multi-agent findings emitted.",
        "# TYPE novaride_multi_agent_findings_total gauge",
        f"novaride_multi_agent_findings_total {int(metrics.get('multi_agent_findings') or len(multi_agent.get('findings') or []))}",
        "# HELP novaride_crisis_max_risk_score Maximum crisis scenario risk score.",
        "# TYPE novaride_crisis_max_risk_score gauge",
        f"novaride_crisis_max_risk_score {int(crisis_summary.get('max_risk_score') or 0)}",
        "# HELP novaride_crisis_critical_scenarios_total Critical crisis scenarios identified.",
        "# TYPE novaride_crisis_critical_scenarios_total gauge",
        f"novaride_crisis_critical_scenarios_total {int(metrics.get('critical_crisis_scenarios') or len(crisis_summary.get('critical_scenarios') or []))}",
        "# HELP novaride_economic_efficiency Cost efficiency score from autonomous optimization.",
        "# TYPE novaride_economic_efficiency gauge",
        f"novaride_economic_efficiency {int(metrics.get('economic_efficiency') or economic.get('cost_efficiency') or 0)}",
        "# HELP novaride_refactor_suggestions_total Total architecture refactor suggestions.",
        "# TYPE novaride_refactor_suggestions_total gauge",
        f"novaride_refactor_suggestions_total {int(metrics.get('refactor_suggestions_total') or len(refactors))}",
    ]
    return "\n".join(lines) + "\n"


def _label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
