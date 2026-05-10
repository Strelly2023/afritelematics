"""
AfriTech Invariant Guard

Enforces runtime invariants BEFORE and AFTER execution.

Responsibilities:
- authority validation
- closed-world enforcement
- replay safety
- deterministic output constraints
- structural guarantees

This module is the runtime-level invariant enforcement layer.

PHASE-1 NOTE:
This file explicitly declares which constitutional invariants
are enforced at the runtime boundary. It does NOT attempt
full semantic discharge yet.
"""

from typing import Any, Set

from afritech.runtime.context.runtime_context import RuntimeContext
from afritech.runtime.engine.executor import ExecutionResult

from afritech.constitution.compiled.invariants_index import (
    I1_REGISTRY_AUTHORITY,
    I2_SEALED_SURFACE,
    I3_NO_SILENT_MUTATION,
    I4_DETERMINISTIC_EXECUTION,
    I8_CLOSED_WORLD,
)


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class InvariantViolation(Exception):
    """Raised when a runtime invariant is violated"""
    pass


# -----------------------------------------------------------------
# INVARIANT DECLARATION (CONSTITUTIONAL WIRING)
# -----------------------------------------------------------------

# These invariants are enforced (or guarded) at runtime.
# Semantic depth will be expanded in later phases.

ENFORCED_INVARIANTS: Set[str] = {
    I1_REGISTRY_AUTHORITY,
    I2_SEALED_SURFACE,
    I3_NO_SILENT_MUTATION,
    I4_DETERMINISTIC_EXECUTION,
    I8_CLOSED_WORLD,
}


# -----------------------------------------------------------------
# GUARD
# -----------------------------------------------------------------

class InvariantGuard:
    """
    Central invariant enforcement class
    """

    # ✅ CLOSED-WORLD AUTHORITY SET
    ALLOWED_AUTHORITIES = {
        "CONSTITUTIONAL_RESEARCH_AGENT",
        "SECONDARY_RESEARCH_AUTHORITY",
    }

    # -----------------------------------------------------------------
    # PRE-EXECUTION CHECKS
    # -----------------------------------------------------------------

    @classmethod
    def enforce_authority(cls, context: RuntimeContext):
        """
        Enforce I1_REGISTRY_AUTHORITY

        Ensure authority belongs to declared registry-backed set.
        """

        if not context.authority_profile:
            raise InvariantViolation("missing_authority_profile")

        if context.authority_profile not in cls.ALLOWED_AUTHORITIES:
            raise InvariantViolation(
                f"unauthorized_authority: {context.authority_profile}"
            )

    @classmethod
    def enforce_closed_world(cls, context: RuntimeContext):
        """
        Enforce I2_SEALED_SURFACE + I8_CLOSED_WORLD

        Ensure no undefined authority or dynamic injection.
        """

        if context.authority_profile not in cls.ALLOWED_AUTHORITIES:
            raise InvariantViolation("closed_world_violation")

    # -----------------------------------------------------------------
    # POST-EXECUTION CHECKS
    # -----------------------------------------------------------------

    @classmethod
    def enforce_replay_valid(cls, result: ExecutionResult):
        """
        Enforce I4_DETERMINISTIC_EXECUTION

        Ensure result is replay-safe and deterministic.
        """

        if not isinstance(result, ExecutionResult):
            raise InvariantViolation("invalid_result_type")

        if not result.context:
            raise InvariantViolation("missing_execution_context")

        context = result.context
        replay = context.replay_requirements or {}

        if replay.get("replay_required", False):

            # ✅ Result must be verifiable
            if not result.verify():
                raise InvariantViolation("result_not_replayable")

            # ✅ Deterministic execution only
            if replay.get("deterministic_only", False):
                cls._check_determinism(result)

            # ✅ Transcript requirement (future-proof)
            if replay.get("transcript_required", False):
                if not hasattr(result, "output"):
                    raise InvariantViolation("missing_transcript")

    # -----------------------------------------------------------------
    # DETERMINISM CHECK
    # -----------------------------------------------------------------

    @staticmethod
    def _check_determinism(result: ExecutionResult):
        """
        Enforce I4_DETERMINISTIC_EXECUTION

        Ensure output is deterministic-safe.
        """

        output = result.output

        if not isinstance(output, dict):
            raise InvariantViolation("non_dict_output")

        # ❗ Ensure JSON-serializable (stable canonical form)
        import json

        try:
            json.dumps(output, sort_keys=True)
        except Exception:
            raise InvariantViolation("non_serializable_output")

    # -----------------------------------------------------------------
    # STRUCTURAL MUTATION PLACEHOLDER
    # -----------------------------------------------------------------

    @classmethod
    def enforce_no_silent_mutation(cls, context: RuntimeContext):
        """
        Enforce I3_NO_SILENT_MUTATION

        Phase‑1 placeholder.
        Full mutation trace validation will be added
        once mutation semantics are saturated.
        """
        # Intentionally non-operative in Phase 1
        return

    # -----------------------------------------------------------------
    # OPTIONAL FUTURE EXTENSIONS
    # -----------------------------------------------------------------

    @classmethod
    def enforce_surface(cls, context: RuntimeContext):
        """
        Placeholder for deeper I2/I8 surface validation
        (future binding to execution_surface registry)
        """
        pass

    @classmethod
    def enforce_epistemic(cls, result: ExecutionResult):
        """
        Placeholder for epistemic constraints
        (future proof saturation)
        """
        pass

    @classmethod
    def enforce_no_side_effects(cls, result: ExecutionResult):
        """
        Placeholder for side-effect isolation
        (future sandbox / audit integration)
        """
        pass