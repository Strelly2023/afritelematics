"""
AfriTech Invariant Guard
========================

Runtime enforcement layer for executable constitutional invariants.

Enforces:

- authority admissibility
- sealed execution boundaries
- deterministic replay semantics
- replay-safe execution validation
- closed-world runtime constraints
"""

from __future__ import annotations

import json

from typing import Set

from afritech.shared.context import RuntimeContext

# -------------------------------------------------------------
# shared execution result
# -------------------------------------------------------------

from afritech.shared.types import (
    ExecutionResult,
)

# -------------------------------------------------------------
# canonical executable runtime invariants
# -------------------------------------------------------------

from afritech.constitution.compiled.invariants_index import (

    I1_REGISTRY_AUTHORITY,
    I2_SEALED_SURFACE,
    I3_NO_SILENT_MUTATION,
    I4_DETERMINISTIC_RUNTIME,
    I5_EPOCH_MONOTONIC,
    I6_CLOSED_EXECUTION_WORLD,
)


# =============================================================
# ERROR
# =============================================================

class InvariantViolation(
    Exception
):
    pass


# =============================================================
# DECLARED RUNTIME ENFORCEMENT
# =============================================================

ENFORCED_INVARIANTS: Set[str] = {

    I1_REGISTRY_AUTHORITY,
    I2_SEALED_SURFACE,
    I3_NO_SILENT_MUTATION,
    I4_DETERMINISTIC_RUNTIME,
    I5_EPOCH_MONOTONIC,
    I6_CLOSED_EXECUTION_WORLD,
}


# =============================================================
# RUNTIME GUARD
# =============================================================

class InvariantGuard:

    """
    Constitutional runtime invariant enforcement.
    """

    # ---------------------------------------------------------
    # constitutional authority surface
    # ---------------------------------------------------------

    ALLOWED_AUTHORITIES = {

        "CONSTITUTIONAL_RESEARCH_AGENT",
        "SECONDARY_RESEARCH_AUTHORITY",
    }

    # =========================================================
    # PRE-EXECUTION ENFORCEMENT
    # =========================================================

    @classmethod
    def enforce_authority(
        cls,
        context: RuntimeContext,
    ) -> None:

        """
        I1_REGISTRY_AUTHORITY
        """

        authority = getattr(
            context,
            "authority_profile",
            None,
        )

        if not authority:

            raise InvariantViolation(
                "missing_authority_profile"
            )

        if authority not in cls.ALLOWED_AUTHORITIES:

            raise InvariantViolation(
                "unauthorized_authority:"
                f" {authority}"
            )

    @classmethod
    def enforce_closed_world(
        cls,
        context: RuntimeContext,
    ) -> None:

        """
        I6_CLOSED_EXECUTION_WORLD
        """

        authority = getattr(
            context,
            "authority_profile",
            None,
        )

        if authority not in cls.ALLOWED_AUTHORITIES:

            raise InvariantViolation(
                "closed_world_violation"
            )

    @classmethod
    def enforce_surface(
        cls,
        context: RuntimeContext,
    ) -> None:

        """
        I2_SEALED_SURFACE
        """

        if not isinstance(
            context,
            RuntimeContext,
        ):

            raise InvariantViolation(
                "invalid_runtime_context"
            )

    @classmethod
    def enforce_no_silent_mutation(
        cls,
        context: RuntimeContext,
    ) -> None:

        """
        I3_NO_SILENT_MUTATION
        """

        if not hasattr(
            context,
            "replay_requirements",
        ):

            raise InvariantViolation(
                "missing_replay_requirements"
            )

    @classmethod
    def enforce_epoch_monotonicity(
        cls,
        context: RuntimeContext,
    ) -> None:

        """
        I5_EPOCH_MONOTONIC
        """

        replay = getattr(
            context,
            "replay_requirements",
            {},
        ) or {}

        epoch = replay.get(
            "epoch"
        )

        if epoch is None:

            raise InvariantViolation(
                "missing_execution_epoch"
            )

        if not isinstance(
            epoch,
            int,
        ):

            raise InvariantViolation(
                "invalid_epoch_type"
            )

        if epoch < 0:

            raise InvariantViolation(
                "negative_epoch_forbidden"
            )

    # =========================================================
    # POST-EXECUTION ENFORCEMENT
    # =========================================================

    @classmethod
    def enforce_replay_valid(
        cls,
        result: ExecutionResult,
    ) -> None:

        """
        I4_DETERMINISTIC_RUNTIME
        """

        if not isinstance(
            result,
            ExecutionResult,
        ):

            raise InvariantViolation(
                "invalid_result_type"
            )

        if not result.context:

            raise InvariantViolation(
                "missing_execution_context"
            )

        context = result.context

        replay = getattr(
            context,
            "replay_requirements",
            {},
        ) or {}

        if replay.get(
            "replay_required",
            False,
        ):

            if not result.verify():

                raise InvariantViolation(
                    "result_not_replayable"
                )

            if replay.get(
                "deterministic_only",
                False,
            ):

                cls._check_determinism(
                    result
                )

            if replay.get(
                "transcript_required",
                False,
            ):

                if not hasattr(
                    result,
                    "output",
                ):

                    raise InvariantViolation(
                        "missing_transcript"
                    )

    # =========================================================
    # DETERMINISM
    # =========================================================

    @staticmethod
    def _check_determinism(
        result: ExecutionResult,
    ) -> None:

        output = result.output

        if not isinstance(
            output,
            dict,
        ):

            raise InvariantViolation(
                "non_dict_output"
            )

        try:

            json.dumps(
                output,
                sort_keys=True,
            )

        except Exception:

            raise InvariantViolation(
                "non_serializable_output"
            )

    # =========================================================
    # PLACEHOLDER ENFORCEMENT
    # =========================================================

    @classmethod
    def enforce_epistemic(
        cls,
        result: ExecutionResult,
    ) -> None:

        """
        Reserved for future epistemic admissibility.
        """

        return

    @classmethod
    def enforce_no_side_effects(
        cls,
        result: ExecutionResult,
    ) -> None:

        """
        Reserved for future side-effect isolation.
        """

        return