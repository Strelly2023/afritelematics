from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from architecture_validator.remediation.model import AutoFix


class KnowledgeGraph:
    def __init__(self) -> None:
        self.graph: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def add_edge(self, issue: str, fix: AutoFix | dict[str, Any], success: bool) -> None:
        fix_payload = fix.as_dict() if isinstance(fix, AutoFix) else dict(fix)
        self.graph[str(issue)].append({"fix": fix_payload, "success": bool(success)})

    def get_best_fix(self, issue: str) -> dict[str, Any] | None:
        entries = self.graph.get(str(issue)) or []
        if not entries:
            return None
        winning = [entry for entry in entries if entry.get("success") is True]
        return (winning or entries)[0].get("fix")

    def summarize(self) -> dict[str, Any]:
        summary: dict[str, Any] = {}
        for issue, entries in self.graph.items():
            summary[issue] = {
                "total": len(entries),
                "success": sum(1 for entry in entries if entry.get("success") is True),
                "fail": sum(1 for entry in entries if entry.get("success") is not True),
                "best_fix": self.get_best_fix(issue),
            }
        return summary
