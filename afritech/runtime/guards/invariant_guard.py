# afritech/runtime/guards/invariant_guard.py

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
"""

from typing import Any
from afritech.runtime.context.runtime_context import RuntimeContext
from afritech.runtime.engine.executor import ExecutionResult


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class InvariantViolation(Exception):
    """Raised when a runtime invariant is violated"""
    pass


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
        Ensure authority belongs to declared system set
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
        Ensure no undefined authority or dynamic injection
        """

        if context.authority_profile not in cls.ALLOWED_AUTHORITIES:
            raise InvariantViolation("closed_world_violation")

    # -----------------------------------------------------------------
    # POST-EXECUTION CHECKS
    # -----------------------------------------------------------------

    @classmethod
    def enforce_replay_valid(cls, result: ExecutionResult):
        """
        Ensure result is replay-safe
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

            # ✅ Deterministic flag enforcement
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
        Ensure output is deterministic-safe
        """

        output = result.output

        if not isinstance(output, dict):
            raise InvariantViolation("non_dict_output")

        # ❗ Ensure JSON-serializable
        import json

        try:
            json.dumps(output, sort_keys=True)
        except Exception:
            raise InvariantViolation("non_serializable_output")

    # -----------------------------------------------------------------
    # OPTIONAL FUTURE EXTENSIONS
    # -----------------------------------------------------------------

    @classmethod
    def enforce_surface(cls, context: RuntimeContext):
        """
        Placeholder for execution surface validation
        (can be bound to execution_scope from certificate)
        """
        # TODO: integrate surface registry check
        pass

    @classmethod
    def enforce_epistemic(cls, result: ExecutionResult):
        """
        Placeholder for epistemic constraints

        Example:
        - no scalar confidence
        - bounded belief systems
        """
        pass

    @classmethod
    def enforce_no_side_effects(cls, result: ExecutionResult):
        """
        Ensure execution does not leak external state

        (future extension via audit logs / sandbox)
        """
        pass
