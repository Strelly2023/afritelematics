"""
AfriTech Step Registry

PURPOSE:
--------
Central registry that maps DSL step names to executable functions.

Responsibilities:
- register step handlers
- resolve step handlers
- validate workflow compatibility
- ensure deterministic lookup

CRITICAL LAW:
-------------
Registry MAY:
- store step mappings
- return step handlers

Registry may NOT:
- execute logic
- modify workflow definitions
- introduce non-determinism
"""

from typing import Callable, Dict, List


# ============================================================
# ✅ STEP REGISTRY
# ============================================================

class StepRegistry:
    """
    Central step registry.

    Guarantees:
    - deterministic lookup
    - safe registration
    - strict validation
    """

    def __init__(self):
        self._steps: Dict[str, Callable] = {}

    # ========================================================
    # ✅ REGISTER STEP
    # ========================================================

    def register(self, name: str, func: Callable):
        """
        Register a step handler.
        """

        if not isinstance(name, str):
            raise TypeError("[DSL ERROR] Step name must be string")

        if not callable(func):
            raise TypeError("[DSL ERROR] Step handler must be callable")

        if name in self._steps:
            raise Exception(f"[DSL ERROR] Step already registered: {name}")

        self._steps[name] = func

    # ========================================================
    # ✅ REGISTER WITH OVERRIDE (EXPLICIT)
    # ========================================================

    def register_override(self, name: str, func: Callable):
        """
        Override existing step (explicitly allowed).
        """

        if not isinstance(name, str):
            raise TypeError("[DSL ERROR] Step name must be string")

        if not callable(func):
            raise TypeError("[DSL ERROR] Step handler must be callable")

        self._steps[name] = func

    # ========================================================
    # ✅ BULK REGISTRATION
    # ========================================================

    def register_bulk(self, steps: Dict[str, Callable]):
        """
        Register multiple steps at once.
        """

        if not isinstance(steps, dict):
            raise TypeError("[DSL ERROR] steps must be a dictionary")

        for name, func in steps.items():
            self.register(name, func)

    # ========================================================
    # ✅ GET STEP
    # ============================================================

    def get(self, name: str) -> Callable:
        """
        Retrieve a step handler.
        """

        if name not in self._steps:
            raise Exception(f"[DSL ERROR] Unknown step: {name}")

        return self._steps[name]

    # ========================================================
    # ✅ SAFE GET
    # ============================================================

    def get_safe(self, name: str):
        """
        Returns None if step does not exist.
        """

        return self._steps.get(name)

    # ========================================================
    # ✅ EXISTS
    # ============================================================

    def exists(self, name: str) -> bool:
        return name in self._steps

    # ========================================================
    # ✅ REMOVE STEP
    # ============================================================

    def remove(self, name: str):
        """
        Remove a step (if exists).
        """

        if name in self._steps:
            del self._steps[name]

    # ========================================================
    # ✅ LIST STEPS
    # ============================================================

    def list(self) -> List[str]:
        """
        List all registered step names (sorted for determinism).
        """

        return sorted(self._steps.keys())

    # ========================================================
    # ✅ COUNT
    # ============================================================

    def count(self) -> int:
        return len(self._steps)

    # ========================================================
    # ✅ CLEAR (TESTING ONLY)
    # ============================================================

    def clear(self):
        """
        Remove all registered steps.
        """

        self._steps.clear()

    # ========================================================
    # ✅ VALIDATE WORKFLOW
    # ============================================================

    def validate_workflow(self, workflow):
        """
        Ensure all workflow steps exist in registry.
        """

        for step in workflow.steps:
            if not self.exists(step.name):
                raise Exception(f"[DSL ERROR] Step not registered: {step.name}")

        return True

    # ========================================================
    # ✅ SNAPSHOT
    # ============================================================

    def snapshot(self) -> Dict[str, str]:
        """
        Return lightweight representation for debugging.
        """

        return {
            "step_count": len(self._steps),
            "steps": self.list(),
        }

    # ========================================================
    # ✅ DETERMINISM CHECK
    # ============================================================

    def validate_determinism(self):
        """
        Ensure registry behaves deterministically.
        """

        s1 = self.list()
        s2 = self.list()

        if s1 != s2:
            raise Exception("[DSL ERROR] Non-deterministic registry order")

        return True

    # ========================================================
    # ✅ DEBUG
    # ============================================================

    def debug(self):
        """
        Human-readable debug view.
        """

        return {
            "total_steps": len(self._steps),
            "steps": self.list(),
        }