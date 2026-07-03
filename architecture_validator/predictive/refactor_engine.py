from __future__ import annotations

from typing import Any


class RefactorEngine:
    def suggest(self, insights: list[dict[str, Any]]) -> list[str]:
        suggestions: list[str] = []
        seen: set[str] = set()
        for insight in insights:
            detail = str(insight.get("detail") or "")
            risk = str(insight.get("risk") or "")
            severity = str(insight.get("severity") or "")
            if "performance" in detail.lower() or risk == "AI_GOVERNANCE_REVIEW":
                suggestion = "Split hot-path execution behind a governed service boundary."
                if suggestion not in seen:
                    seen.add(suggestion)
                    suggestions.append(suggestion)
            if "cost" in detail.lower() or severity == "medium":
                suggestion = "Consolidate low-traffic services behind shared runtime capacity."
                if suggestion not in seen:
                    seen.add(suggestion)
                    suggestions.append(suggestion)
            if risk in {"SECURITY_RISK", "REPLAY_OR_TRUST_DRIFT"}:
                suggestion = "Add policy guardrails and replay gates before further expansion."
                if suggestion not in seen:
                    seen.add(suggestion)
                    suggestions.append(suggestion)
        return suggestions
