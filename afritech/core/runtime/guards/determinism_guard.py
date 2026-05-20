# afritech/runtime/guards/determinism_guard.py

"""
AfriTech DeterminismGuard (AST-Level)
====================================

Enforces deterministic execution by statically inspecting
the execution function using Python AST.

ABSOLUTE RULE:
- If forbidden nondeterministic constructs are present,
  execution MUST be halted before runtime.

This guard performs NO execution.
"""

from __future__ import annotations

import ast
import inspect
from typing import Set, Optional


# ---------------------------------------------------------------------
# ERROR
# ---------------------------------------------------------------------

class DeterminismViolation(Exception):
    """
    Raised when non-deterministic constructs are detected.
    """
    pass


# ---------------------------------------------------------------------
# FORBIDDEN SEMANTIC SURFACES
# ---------------------------------------------------------------------

FORBIDDEN_CALLS: Set[str] = {
    # time
    "time.time",
    "time.sleep",
    "datetime.datetime.now",
    "datetime.datetime.utcnow",

    # randomness
    "random.random",
    "random.randint",
    "random.choice",
    "random.shuffle",
    "random.uniform",

    # environment / OS
    "os.environ",
    "os.getenv",

    # concurrency
    "threading.Thread",
    "asyncio.create_task",

    # I/O / network
    "open",
    "socket.socket",
    "requests.get",
    "requests.post",
}

FORBIDDEN_MODULES: Set[str] = {
    "time",
    "random",
    "os",
    "socket",
    "threading",
    "asyncio",
    "requests",
}


# ---------------------------------------------------------------------
# AST VISITOR
# ---------------------------------------------------------------------

class _DeterminismVisitor(ast.NodeVisitor):
    """
    Walks the AST and records forbidden constructs.
    """

    def __init__(self) -> None:
        self.violations: list[str] = []

    # -------------------------------------------------------------
    # IMPORTS
    # -------------------------------------------------------------

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".")[0]
            if root in FORBIDDEN_MODULES:
                self.violations.append(
                    f"forbidden_import:{alias.name}"
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            root = node.module.split(".")[0]
            if root in FORBIDDEN_MODULES:
                self.violations.append(
                    f"forbidden_import:{node.module}"
                )
        self.generic_visit(node)

    # -------------------------------------------------------------
    # FUNCTION CALLS
    # -------------------------------------------------------------

    def visit_Call(self, node: ast.Call) -> None:
        call_name = self._resolve_call_name(node.func)
        if call_name and call_name in FORBIDDEN_CALLS:
            self.violations.append(
                f"forbidden_call:{call_name}"
            )
        self.generic_visit(node)

    # -------------------------------------------------------------
    # NAME RESOLUTION
    # -------------------------------------------------------------

    def _resolve_call_name(self, node: ast.AST) -> Optional[str]:
        """
        Resolve fully-qualified call name if possible.

        Examples:
        - time.time()        -> "time.time"
        - random.randint()  -> "random.randint"
        - os.environ.get()  -> "os.environ"
        """

        # Simple function call: foo()
        if isinstance(node, ast.Name):
            return node.id

        # Attribute chain: a.b.c()
        if isinstance(node, ast.Attribute):
            parts: list[str] = []
            current = node

            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value

            if isinstance(current, ast.Name):
                parts.append(current.id)
                return ".".join(reversed(parts))

        return None


# ---------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------

def enforce_determinism(*, execution_fn) -> None:
    """
    Enforce determinism on the provided execution function.

    This MUST be called before execution.

    :param execution_fn: the execution function to inspect
    :raises DeterminismViolation: if nondeterministic constructs are found
    """

    try:
        source = inspect.getsource(execution_fn)
    except Exception as e:
        raise DeterminismViolation(
            f"Cannot retrieve source for execution function: {e}"
        )

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise DeterminismViolation(
            f"Unable to parse execution function AST: {e}"
        )

    visitor = _DeterminismVisitor()
    visitor.visit(tree)

    if visitor.violations:
        formatted = "\n".join(f" - {v}" for v in visitor.violations)
        raise DeterminismViolation(
            "Non-deterministic constructs detected:\n"
            f"{formatted}"
        )
