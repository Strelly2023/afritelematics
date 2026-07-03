from __future__ import annotations

from typing import Any


class Optimizer:
    def analyze(self, patterns: dict[str, dict[str, int]]) -> list[str]:
        suggestions: list[str] = []
        for issue, stats in patterns.items():
            if stats.get("fail", 0) > stats.get("success", 0):
                suggestions.append(f"Improve rule or fix strategy for: {issue}")
            if stats.get("success", 0) >= 3 and stats.get("fail", 0) == 0:
                suggestions.append(f"Promote stable remediation pattern for: {issue}")
        return suggestions

    def risk_profile(self, patterns: dict[str, dict[str, int]]) -> dict[str, Any]:
        total_fail = sum(stats.get("fail", 0) for stats in patterns.values())
        total_success = sum(stats.get("success", 0) for stats in patterns.values())
        total = total_fail + total_success
        if total == 0:
            return {"risk": "unknown", "score": 0}
        score = int(round((total_success / total) * 100))
        if score >= 90:
            risk = "low"
        elif score >= 70:
            risk = "medium"
        else:
            risk = "high"
        return {"risk": risk, "score": score, "total": total, "success": total_success, "fail": total_fail}
