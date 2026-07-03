from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from architecture_validator.remediation.model import AutoFix


class LearningEngine:
    def __init__(self, memory_path: str | Path = "architecture_learning_memory.json") -> None:
        self.memory_path = Path(memory_path)
        self.memory: list[dict[str, Any]] = self._load()

    def record_event(self, issue: str, fix: AutoFix | dict[str, Any], success: bool) -> None:
        payload = {
            "issue": issue,
            "fix": fix.as_dict() if isinstance(fix, AutoFix) else dict(fix),
            "success": bool(success),
        }
        self.memory.append(payload)
        self._save()

    def learn_patterns(self) -> dict[str, dict[str, int]]:
        patterns: dict[str, dict[str, int]] = {}
        for event in self.memory:
            issue = str(event.get("issue") or "unknown")
            bucket = patterns.setdefault(issue, {"success": 0, "fail": 0})
            if event.get("success") is True:
                bucket["success"] += 1
            else:
                bucket["fail"] += 1
        return patterns

    def _load(self) -> list[dict[str, Any]]:
        if not self.memory_path.exists():
            return []
        try:
            payload = json.loads(self.memory_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        return payload if isinstance(payload, list) else []

    def _save(self) -> None:
        self.memory_path.write_text(
            json.dumps(self.memory, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
