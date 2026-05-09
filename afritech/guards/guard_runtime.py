# afritech/guards/guard_runtime.py

"""
AfriTech Runtime Guards

Purpose:
Provide concrete runtime enforcement guards aligned with the
constitutional engine (engine.py).

Guarantees:
- fail-fast behavior (via fail → ConstitutionalViolation)
- deterministic outcomes
- no silent failures
- compatibility with GuardCore adapter

These guards operate directly on execution context.
"""

from typing import Dict, Any

from afritech.guards.guard_core import Guard
from afritech.guards.engine import ViolationClass


# -----------------------------------------------------------------
# TRACE GUARD
# -----------------------------------------------------------------

class TraceGuard(Guard):

    def enforce(self, context: Dict[str, Any]):

        event = context.get("trace_event")

        if not event:
            return self.fail(
                "missing_trace_event",
                ViolationClass.B_STRUCTURAL,
            )

        expected = event.get("computed_hash")
        actual = event.get("event_hash")

        if not expected or not actual:
            return self.fail(
                "trace_hash_missing",
                ViolationClass.B_STRUCTURAL,
            )

        if expected != actual:
            return self.fail(
                "trace_integrity_violation",
                ViolationClass.A_FATAL,
            )

        return True


# -----------------------------------------------------------------
# STATE GUARD
# -----------------------------------------------------------------

class StateGuard(Guard):

    def enforce(self, context: Dict[str, Any]):

        current = context.get("current_state")
        target = context.get("target_state")
        allowed = context.get("allowed_transitions", [])

        if current is None or target is None:
            return self.fail(
                "state_context_missing",
                ViolationClass.B_STRUCTURAL,
            )

        if not isinstance(allowed, (list, set, tuple)):
            return self.fail(
                "invalid_allowed_transitions_structure",
                ViolationClass.B_STRUCTURAL,
            )

        if (current, target) not in allowed:
            return self.fail(
                f"illegal_transition: {current} → {target}",
                ViolationClass.A_FATAL,
            )

        return True


# -----------------------------------------------------------------
# AUTHORITY GUARD
# -----------------------------------------------------------------

class AuthorityGuard(Guard):

    def enforce(self, context: Dict[str, Any]):

        authority = context.get("authority")
        genesis_hash = context.get("genesis_hash")

        if not authority:
            return self.fail(
                "missing_authority",
                ViolationClass.A_FATAL,
            )

        if not genesis_hash:
            return self.fail(
                "missing_genesis_hash",
                ViolationClass.B_STRUCTURAL,
            )

        if authority.get("root") != genesis_hash:
            return self.fail(
                "authority_not_derived_from_genesis",
                ViolationClass.A_FATAL,
            )

        return True


# -----------------------------------------------------------------
# INVARIANT GUARD
# -----------------------------------------------------------------

class RuntimeInvariantGuard(Guard):

    def enforce(self, context: Dict[str, Any]):

        violations = context.get("invariant_violations", [])

        if not isinstance(violations, list):
            return self.fail(
                "invalid_invariant_structure",
                ViolationClass.B_STRUCTURAL,
            )

        if violations:
            return self.fail(
                f"invariant_violation: {violations}",
                ViolationClass.A_FATAL,
            )

        return True


# -----------------------------------------------------------------
# UNDEFINED BEHAVIOR GUARD (CRITICAL SAFETY)
# -----------------------------------------------------------------

class UndefinedBehaviorGuard(Guard):

    def enforce(self, context: Dict[str, Any]):

        if context.get("undefined_behavior"):
            return self.fail(
                "undefined_behavior_detected",
                ViolationClass.A_FATAL,
            )

        return True


# -----------------------------------------------------------------
# CONTEXT VALIDATION GUARD (SANITY CHECK)
# -----------------------------------------------------------------

class ContextGuard(Guard):

    def enforce(self, context: Dict[str, Any]):

        if not isinstance(context, dict):
            return self.fail(
                "context_not_dict",
                ViolationClass.B_STRUCTURAL,
            )

        # Optional strict mode
        if not context:
            return self.fail(
                "empty_context",
                ViolationClass.C_DOCUMENTARY,
            )

        return True