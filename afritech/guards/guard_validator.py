# afritech/guards/guard_validator.py

"""
AfriTech Guard Validator

Purpose:
Validate guard registry and configuration under constitutional rules.

Guarantees:
- deterministic validation
- no duplicate guards
- valid guard structure
- required fields enforced
- no invalid guard definitions allowed

All failures -> engine.fail() -> ConstitutionalViolation
"""

from typing import Dict, Any, List

from afritech.guards.engine import fail, ViolationClass


# -----------------------------------------------------------------
# VALID GUARD TYPES (CANONICAL)
# -----------------------------------------------------------------

VALID_GUARD_TYPES = {
    "INVARIANT_GUARD",
    "AUTHORITY_GUARD",
    "EPOCH_GUARD",
    "RUNTIME_GUARD",
    "TRACE_GUARD",
    "STATE_GUARD",
}


# -----------------------------------------------------------------
# VALIDATOR
# -----------------------------------------------------------------

class GuardValidator:

    # =============================================================
    # ENTRYPOINT
    # =============================================================

    @classmethod
    def validate_registry(cls, registry: Dict[str, Any]) -> bool:
        """
        Validate full guard registry.

        Expected structure:
        {
            "guard_registry": {
                "guards": [...]
            }
        }
        """

        if not isinstance(registry, dict):
            fail("invalid_registry_structure", ViolationClass.B_STRUCTURAL)

        if "guard_registry" not in registry:
            fail("missing_guard_registry", ViolationClass.B_STRUCTURAL)

        data = registry["guard_registry"]

        if not isinstance(data, dict):
            fail("invalid_guard_registry_block", ViolationClass.B_STRUCTURAL)

        guards = data.get("guards")

        if not isinstance(guards, list):
            fail("guards_not_list", ViolationClass.B_STRUCTURAL)

        if not guards:
            fail("empty_guard_registry", ViolationClass.A_FATAL)

        cls._validate_guards(guards)

        return True

    # =============================================================
    # VALIDATE GUARDS
    # =============================================================

    @staticmethod
    def _validate_guards(guards: List[Dict[str, Any]]):

        seen_ids = set()

        for g in guards:

            if not isinstance(g, dict):
                fail("invalid_guard_entry", ViolationClass.B_STRUCTURAL)

            guard_id = g.get("id")
            guard_type = g.get("type")
            target = g.get("target")

            # -----------------------------------------------------
            # REQUIRED FIELDS
            # -----------------------------------------------------

            if not guard_id:
                fail("missing_guard_id", ViolationClass.B_STRUCTURAL)

            if not guard_type:
                fail("missing_guard_type", ViolationClass.B_STRUCTURAL)

            if not target:
                fail("missing_guard_target", ViolationClass.B_STRUCTURAL)

            # -----------------------------------------------------
            # UNIQUE ID
            # -----------------------------------------------------

            if guard_id in seen_ids:
                fail(
                    f"duplicate_guard_id: {guard_id}",
                    ViolationClass.B_STRUCTURAL,
                )

            seen_ids.add(guard_id)

            # -----------------------------------------------------
            # VALID TYPE
            # -----------------------------------------------------

            if guard_type not in VALID_GUARD_TYPES:
                fail(
                    f"invalid_guard_type: {guard_type}",
                    ViolationClass.B_STRUCTURAL,
                )

            # -----------------------------------------------------
            # STRING STRUCTURE CHECKS
            # -----------------------------------------------------

            if not isinstance(guard_id, str):
                fail("guard_id_not_string", ViolationClass.B_STRUCTURAL)

            if not isinstance(guard_type, str):
                fail("guard_type_not_string", ViolationClass.B_STRUCTURAL)

            if not isinstance(target, str):
                fail("guard_target_not_string", ViolationClass.B_STRUCTURAL)

            # -----------------------------------------------------
            # OPTIONAL RULE
            # -----------------------------------------------------

            if "rule" in g and not isinstance(g["rule"], str):
                fail("invalid_guard_rule", ViolationClass.B_STRUCTURAL)

    # =============================================================
    # SAFE VALIDATION
    # =============================================================

    @classmethod
    def try_validate_registry(cls, registry: Dict[str, Any]) -> bool:
        """
        Safe validation (no crash)
        """

        try:
            return cls.validate_registry(registry)
        except SystemExit:
            return False

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self):
        return "<GuardValidator strict>"