from __future__ import annotations

from django.db import OperationalError, ProgrammingError

from afritech.models import GovernanceRule, RuleDependency


def build_rule_graph() -> dict[str, dict[str, list[str]]]:
    graph: dict[str, dict[str, list[str]]] = {}
    try:
        for rule in GovernanceRule.objects.all():
            graph[rule.name] = {"requires": [], "conflicts": [], "influences": []}
        for dependency in RuleDependency.objects.select_related("from_rule", "to_rule"):
            graph.setdefault(
                dependency.from_rule.name,
                {"requires": [], "conflicts": [], "influences": []},
            )
            graph[dependency.from_rule.name][dependency.dependency_type].append(
                dependency.to_rule.name
            )
    except (OperationalError, ProgrammingError):
        return {}
    return graph
