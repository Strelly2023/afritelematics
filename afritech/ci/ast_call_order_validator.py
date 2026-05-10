# afritech/ci/ast_call_order_validator.py

"""
AfriTech CI — AST Call Order Validator
=====================================

This validator enforces constitutional EXECUTION order
ONLY at the constitutional execution gateway.

IMPORTANT:
- Replay is a constitutional VERIFIER, not an executor.
- Replay MUST NOT be forced to perform execution steps.
- Enforcing execution order on replay is a category error.

This validator is:
- Fail-closed
- Topology-aware
- Authority-correct
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import List


# ---------------------------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------
# CONSTITUTIONAL EXECUTION ENTRYPOINT (SINGULAR)
# ---------------------------------------------------------------------

EXECUTION_ENTRYPOINT = "afritech/kernel/constitutional_gateway.py"


# ---------------------------------------------------------------------
# REQUIRED EXECUTION CALL SEQUENCE (GATEWAY ONLY)
# ---------------------------------------------------------------------

CALL_SEQUENCE = [
    "assert_runtime_admission_legality",
    "validate_state_mutation",
    "apply_state_transition",
    "assert_execution_legality",
    "canonicalize_trace",
    "hash_canonical_trace",
    "from_context",  # ConstitutionalReceipt.from_context
]


# ---------------------------------------------------------------------
# FAILURE HANDLER
# ---------------------------------------------------------------------

def fail(violations: List[str]) -> None:
    print("❌ CONSTITUTIONAL CALL ORDER VIOLATIONS DETECTED")
    for v in sorted(set(violations)):
        print("  -", v)
    sys.exit(1)


# ---------------------------------------------------------------------
# AST VISITOR
# ---------------------------------------------------------------------

class CallOrderVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls: List[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        name = self._resolve_call_name(node.func)
        if name:
            self.calls.append(name)
        self.generic_visit(node)

    @staticmethod
    def _resolve_call_name(func) -> str | None:
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return None


# ---------------------------------------------------------------------
# VALIDATION LOGIC
# ---------------------------------------------------------------------

def validate_call_order(calls: List[str], path: Path) -> List[str]:
    violations: List[str] = []
    last_index = -1

    for required in CALL_SEQUENCE:
        if required not in calls:
            violations.append(
                f"{path}: missing required constitutional call '{required}'"
            )
            continue

        index = calls.index(required)

        if index < last_index:
            violations.append(
                f"{path}: constitutional call '{required}' "
                f"occurs before a required predecessor"
            )

        last_index = index

    return violations


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main() -> None:
    violations: List[str] = []

    path = PROJECT_ROOT / EXECUTION_ENTRYPOINT
    if not path.exists():
        fail([f"Missing constitutional execution entrypoint: {EXECUTION_ENTRYPOINT}"])

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as e:
        fail([f"Failed to parse {EXECUTION_ENTRYPOINT}: {e}"])

    visitor = CallOrderVisitor()
    visitor.visit(tree)

    violations.extend(validate_call_order(visitor.calls, path))

    if violations:
        fail(violations)

    print("✅ AST call order validated — constitutional execution order enforced")


# ---------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()