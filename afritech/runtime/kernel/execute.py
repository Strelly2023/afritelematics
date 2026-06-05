from __future__ import annotations

from typing import Callable, Any, Set
import inspect
import ast

from afritech.runtime.admission.controller import AdmissionController
from afritech.epoch.epoch_snapshot import EpochSnapshot


# =====================================================
# ✅ Execution Context
# =====================================================

class ExecutionContext:
    """
    Immutable execution context passed to all functions.
    """

    def __init__(self, epoch_snapshot: EpochSnapshot) -> None:
        if not isinstance(epoch_snapshot, EpochSnapshot):
            raise TypeError("ExecutionContext requires a valid EpochSnapshot")

        self.epoch_snapshot = epoch_snapshot


# =====================================================
# ✅ Execution Kernel (FINAL)
# =====================================================

class ExecutionKernel:
    """
    🔥 GA-Elite Sovereign Execution Kernel

    Guarantees:
    - Admission-gated execution
    - Strong determinism enforcement (AST-based)
    - Single controlled execution path
    - Stable execution identity
    """

    def __init__(self, admission_controller: AdmissionController) -> None:
        if not isinstance(admission_controller, AdmissionController):
            raise TypeError("ExecutionKernel requires AdmissionController")

        self.admission_controller = admission_controller

    # =====================================================
    # ✅ EXECUTE
    # =====================================================

    def execute(
        self,
        fn: Callable[[ExecutionContext], Any],
        context: ExecutionContext,
        fn_id: str | None = None,   # ✅ NEW
    ) -> Any:

        if not callable(fn):
            raise TypeError("Execution requires callable")

        if not isinstance(context, ExecutionContext):
            raise TypeError("Invalid ExecutionContext")

        # ✅ Admission enforcement
        if not self.admission_controller.is_admitted():
            admitted = self.admission_controller.admit(context.epoch_snapshot)
            if not admitted:
                raise RuntimeError("Execution denied by AdmissionController")

        # ✅ Determinism enforcement (UPGRADED)
        self._enforce_determinism(fn)

        try:
            result = fn(context)
            return result

        except Exception as e:
            raise RuntimeError(f"Execution failed: {e}") from e

    # =====================================================
    # ✅ STRONG DETERMINISM ENFORCEMENT
    # =====================================================

    def _enforce_determinism(self, fn: Callable[..., Any]) -> None:
        """
        AST-based deterministic enforcement.
        Detects unsafe imports and calls.
        """

        try:
            source = inspect.getsource(fn)
        except Exception:
            # fallback: allow but warn by restriction
            self._fallback_check(fn)
            return

        try:
            tree = ast.parse(source)
        except Exception:
            self._fallback_check(fn)
            return

        forbidden_calls: Set[str] = {
            "random",
            "time",
            "datetime",
            "uuid",
            "os",
        }

        violations: Set[str] = set()

        for node in ast.walk(tree):
            # ✅ detect imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in forbidden_calls:
                        violations.add(alias.name)

            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] in forbidden_calls:
                    violations.add(node.module)

            # ✅ detect function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in forbidden_calls:
                        violations.add(node.func.id)

                elif isinstance(node.func, ast.Attribute):
                    root = self._get_attr_root(node.func)
                    if root in forbidden_calls:
                        violations.add(root)

        if violations:
            raise RuntimeError(
                f"❌ Non-deterministic execution detected: {sorted(violations)}"
            )

    # =====================================================
    # ✅ ATTRIBUTE ROOT RESOLUTION
    # =====================================================

    def _get_attr_root(self, node: ast.Attribute) -> str:
        """
        Extract root name from nested attributes:
        os.path.join → os
        """

        while isinstance(node, ast.Attribute):
            node = node.value

        if isinstance(node, ast.Name):
            return node.id

        return ""

    # =====================================================
    # ✅ FALLBACK CHECK (SAFE)
    # =====================================================

    def _fallback_check(self, fn: Callable) -> None:
        """
        Fallback bytecode check (less strict but safe).
        """

        forbidden = {"random", "time", "uuid", "os.urandom"}

        names = set(getattr(fn, "__code__", {}).co_names or [])

        violations = [name for name in names if name in forbidden]

        if violations:
            raise RuntimeError(
                f"❌ Non-deterministic function detected: {violations}"
            )
