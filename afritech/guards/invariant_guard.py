# afritech/guards/invariant_guard.py

"""
Invariant Guard (Constitution-Aligned)

Enforces core invariants:
- I4: deterministic execution
- I5: replay validity
- I6: authority presence
- I8: closed world assumption
- I9: proof requirement

All failures delegate to engine.fail() via Guard.fail().
"""

from typing import Dict, Any

from afritech.guards.guard_core import Guard
from afritech.guards.engine import ViolationClass


# -----------------------------------------------------------------
# INVARIANT GUARD
# -----------------------------------------------------------------

class InvariantGuard(Guard):

    def enforce(self, context: Dict[str, Any]):

        # ---------------------------------------------------------
        # Basic context validation (CRITICAL HARDENING)
        # ---------------------------------------------------------

        if not isinstance(context, dict):
            return self.fail(
                "invalid_context_structure",
                ViolationClass.B_STRUCTURAL,
            )

        # ---------------------------------------------------------
        # I4 — Deterministic Execution
        # ---------------------------------------------------------

        original = context.get("original_result")
        replay = context.get("replay_result")

        # Only enforce if both supplied (safe partial replay mode)
        if original is not None and replay is not None:

            if not hasattr(original, "result_hash") or not hasattr(replay, "result_hash"):
                return self.fail(
                    "missing_result_hash",
                    ViolationClass.B_STRUCTURAL,
                )

            if original.result_hash != replay.result_hash:
                return self.fail(
                    "deterministic_execution_violation",
                    ViolationClass.A_FATAL,
                )

        # ---------------------------------------------------------
        # I5 — Replay Validity
        # ---------------------------------------------------------

        replay_result = context.get("replay_result")

        if replay_result is not None:

            if not hasattr(replay_result, "success"):
                return self.fail(
                    "invalid_replay_result_structure",
                    ViolationClass.B_STRUCTURAL,
                )

            if not replay_result.success:
                return self.fail(
                    "replay_invalid",
                    ViolationClass.A_FATAL,
                )

        # ---------------------------------------------------------
        # I6 — Authority declared
        # ---------------------------------------------------------

        context_obj = context.get("runtime_context")

        if context_obj is not None:

            if not hasattr(context_obj, "authority_profile"):
                return self.fail(
                    "invalid_runtime_context_structure",
                    ViolationClass.B_STRUCTURAL,
                )

            if not context_obj.authority_profile:
                return self.fail(
                    "missing_authority",
                    ViolationClass.A_FATAL,
                )

        # ---------------------------------------------------------
        # I8 — Closed world
        # ---------------------------------------------------------

        if context_obj is not None:

            if not hasattr(context_obj, "payload"):
                return self.fail(
                    "missing_payload",
                    ViolationClass.B_STRUCTURAL,
                )

            if not isinstance(context_obj.payload, dict):
                return self.fail(
                    "closed_world_violation",
                    ViolationClass.B_STRUCTURAL,
                )

        # ---------------------------------------------------------
        # I9 — Proof required
        # ---------------------------------------------------------

        proof = context.get("proof")

        if proof is None:
            return self.fail(
                "missing_proof",
                ViolationClass.A_FATAL,
            )

        if not isinstance(proof, dict):
            return self.fail(
                "invalid_proof_structure",
                ViolationClass.B_STRUCTURAL,
            )

        # ---------------------------------------------------------
        # PASS
        # ---------------------------------------------------------

        return True