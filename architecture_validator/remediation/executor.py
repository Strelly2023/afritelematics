from __future__ import annotations

import json
from pathlib import Path

from architecture_validator.remediation.model import AutoFix, FixExecutionResult


class FixExecutor:
    def __init__(self, artifact_path: str | Path = "architecture_remediation_report.json") -> None:
        self.artifact_path = Path(artifact_path)

    def execute(
        self,
        fixes: list[AutoFix],
        *,
        apply: bool = False,
        allow_risky: bool = False,
    ) -> list[FixExecutionResult]:
        results: list[FixExecutionResult] = []
        for fix in fixes:
            if not apply:
                results.append(
                    FixExecutionResult(
                        fix=fix,
                        status="proposed",
                        message="Remediation plan generated; no source changes applied.",
                    )
                )
                continue

            if fix.safe_to_apply or allow_risky:
                results.append(self._apply_fix(fix))
            else:
                results.append(
                    FixExecutionResult(
                        fix=fix,
                        status="manual_review_required",
                        message="Fix is high-risk and requires human approval.",
                    )
                )

        if apply:
            self._write_artifact(results)
        return results

    def _apply_fix(self, fix: AutoFix) -> FixExecutionResult:
        return FixExecutionResult(
            fix=fix,
            status="recorded",
            message="Remediation action recorded for governed review.",
            artifact=str(self.artifact_path),
        )

    def _write_artifact(self, results: list[FixExecutionResult]) -> None:
        payload = [result.as_dict() for result in results]
        self.artifact_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
