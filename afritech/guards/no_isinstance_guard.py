"""
afritech.guards.no_isinstance_guard

Guard to prevent forbidden isinstance() usage on distributed core types.

Purpose:
- enforce invariant I31_STRUCTURAL_VALIDATION_REQUIRED
- allow safe Python isinstance usage
- forbid fragile class identity coupling in distributed core
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Tuple


# ============================================================
# ERROR
# ============================================================

class NoIsinstanceViolationError(RuntimeError):
    """Raised when forbidden isinstance usage is detected."""


# ============================================================
# CONFIG
# ============================================================

@dataclass(frozen=True)
class GuardConfig:
    root_path: str = "afritech/distributed"

    # ✅ ONLY forbid these (distributed core identities)
    forbidden_types: Tuple[str, ...] = (
        "DistributedQueueRecord",
        "WorkerResult",
        "ExecutionTrace",
        "QueueRecordBatch",
    )

    # ✅ Allow standard safe types
    allowed_types: Tuple[str, ...] = (
        "str",
        "int",
        "float",
        "dict",
        "list",
        "tuple",
        "set",
        "bool",
        "type",
        "Exception",
    )

    # ✅ Allowlist paths (optional exemptions)
    allowed_paths: Tuple[str, ...] = ()


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class GuardViolation:
    file_path: str
    line_number: int
    line: str
    matched_type: str

    def format(self) -> str:
        return (
            f"{self.file_path}:{self.line_number} "
            f"[{self.matched_type}] -> {self.line.strip()}"
        )


# ============================================================
# SCANNER
# ============================================================

class NoIsinstanceGuard:
    """
    Scans codebase and detects forbidden isinstance usage.
    """

    def __init__(self, config: GuardConfig | None = None):
        self.config = config or GuardConfig()

    # ---------------------------------------------------------
    # MAIN
    # ---------------------------------------------------------

    def run(self) -> None:
        violations = self._scan()

        if violations:
            message = "\n".join(v.format() for v in violations)

            raise NoIsinstanceViolationError(
                f"Forbidden isinstance usage detected:\n{message}"
            )

        print("✅ NoIsinstanceGuard PASSED")

    # ---------------------------------------------------------
    # SCAN LOGIC
    # ---------------------------------------------------------

    def _scan(self) -> List[GuardViolation]:
        violations: List[GuardViolation] = []

        for root, _, files in os.walk(self.config.root_path):
            for filename in files:
                if not filename.endswith(".py"):
                    continue

                path = os.path.join(root, filename)

                # ✅ Skip allowed paths
                if any(allowed in path for allowed in self.config.allowed_paths):
                    continue

                violations.extend(self._scan_file(path))

        return violations

    def _scan_file(self, path: str) -> List[GuardViolation]:
        violations: List[GuardViolation] = []

        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        except Exception:
            return violations

        for idx, line in enumerate(lines, start=1):
            if "isinstance(" not in line:
                continue

            # ✅ detect forbidden types
            for forbidden in self.config.forbidden_types:
                if forbidden in line and not self._is_allowed(line):
                    violations.append(
                        GuardViolation(
                            file_path=path,
                            line_number=idx,
                            line=line,
                            matched_type=forbidden,
                        )
                    )

        return violations

    # ---------------------------------------------------------
    # FILTERING
    # ---------------------------------------------------------

    def _is_allowed(self, line: str) -> bool:
        """
        Allow safe Python patterns.
        """
        for allowed in self.config.allowed_types:
            if allowed in line:
                return True
        return False


# ============================================================
# ENTRYPOINT
# ============================================================

def main() -> int:
    guard = NoIsinstanceGuard()

    try:
        guard.run()
        return 0
    except NoIsinstanceViolationError as exc:
        print(f"❌ {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())