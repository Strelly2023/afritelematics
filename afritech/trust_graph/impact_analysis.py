from __future__ import annotations

from .dependency_engine import build_rule_graph


def analyze_rule_change(rule_name: str) -> list[str]:
    graph = build_rule_graph()
    impacted: set[str] = set()

    def traverse(current: str) -> None:
        for dep_type in ("requires", "influences"):
            for target in graph.get(current, {}).get(dep_type, []):
                if target not in impacted:
                    impacted.add(target)
                    traverse(target)

    traverse(rule_name)
    return sorted(impacted)


def detect_conflicts(rule_name: str) -> list[str]:
    graph = build_rule_graph()
    return sorted(graph.get(rule_name, {}).get("conflicts", []))
