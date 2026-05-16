"""
AfriTech Invariant Guard
"""

from typing import Any, Set
from afritech.shared.context import RuntimeContext

# ✅ FIXED: import from shared (removes cycle)
from afritech.shared.types import ExecutionResult

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
    pass


# -----------------------------------------------------------------
# INVARIANT DECLARATION
# -----------------------------------------------------------------

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

    ALLOWED_AUTHORITIES = {
        "CONSTITUTIONAL_RESEARCH_AGENT",
        "SECONDARY_RESEARCH_AUTHORITY",
    }

    # ---------------- PRE ----------------

    @classmethod
    def enforce_authority(cls, context: RuntimeContext):

        if not context.authority_profile:
            raise InvariantViolation("missing_authority_profile")

        if context.authority_profile not in cls.ALLOWED_AUTHORITIES:
            raise InvariantViolation(
                f"unauthorized_authority: {context.authority_profile}"
            )

    @classmethod
    def enforce_closed_world(cls, context: RuntimeContext):

        if context.authority_profile not in cls.ALLOWED_AUTHORITIES:
            raise InvariantViolation("closed_world_violation")

    # ---------------- POST ----------------

    @classmethod
    def enforce_replay_valid(cls, result: ExecutionResult):

        if not isinstance(result, ExecutionResult):
            raise InvariantViolation("invalid_result_type")

        if not result.context:
            raise InvariantViolation("missing_execution_context")

        context = result.context
        replay = context.replay_requirements or {}

        if replay.get("replay_required", False):

            if not result.verify():
                raise InvariantViolation("result_not_replayable")

            if replay.get("deterministic_only", False):
                cls._check_determinism(result)

            if replay.get("transcript_required", False):
                if not hasattr(result, "output"):
                    raise InvariantViolation("missing_transcript")

    # ---------------- DETERMINISM ----------------

    @staticmethod
    def _check_determinism(result: ExecutionResult):

        output = result.output

        if not isinstance(output, dict):
            raise InvariantViolation("non_dict_output")

        import json

        try:
            json.dumps(output, sort_keys=True)
        except Exception:
            raise InvariantViolation("non_serializable_output")

    # ---------------- PLACEHOLDERS ----------------

    @classmethod
    def enforce_no_silent_mutation(cls, context: RuntimeContext):
        return

    @classmethod
    def enforce_surface(cls, context: RuntimeContext):
        pass

    @classmethod
    def enforce_epistemic(cls, result: ExecutionResult):
        pass

    @classmethod
    def enforce_no_side_effects(cls, result: ExecutionResult):
        pass
