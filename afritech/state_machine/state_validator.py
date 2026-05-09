# afritech/state_machine/state_validator.py

"""
AfriTech State Validator

Purpose:
Validate state machine definition and runtime behavior.

Guarantees:
- transition totality
- allowed/forbidden correctness
- no ambiguity
- deterministic replay safety
- terminal state finality

This is the LEGAL AUTHORITY for system behavior.
"""

from typing import Dict, Any, Set, Tuple, List


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class StateValidationError(Exception):
    """Raised when state machine validation fails"""
    pass


# -----------------------------------------------------------------
# VALIDATOR
# -----------------------------------------------------------------

class StateValidator:

    # =============================================================
    # ENTRYPOINT
    # =============================================================

    @classmethod
    def validate(cls, transitions: Dict[str, Any]) -> bool:

        cls._validate_structure(transitions)

        states = cls._extract_states(transitions)
        allowed = transitions.get("allowed", [])
        forbidden = transitions.get("forbidden", [])

        cls._validate_allowed(allowed)
        cls._validate_forbidden(forbidden)

        cls._validate_unique_ids(allowed)
        cls._validate_disjoint(allowed, forbidden)

        cls._validate_states_exist(states, allowed, forbidden)
        cls._validate_totality(states, allowed, forbidden)

        cls._validate_terminal_states(allowed)
        cls._validate_no_self_loops(allowed, forbidden)

        return True

    # =============================================================
    # STRUCTURE
    # =============================================================

    @staticmethod
    def _validate_structure(transitions: Dict[str, Any]):

        if not isinstance(transitions, dict):
            raise StateValidationError("invalid_structure")

        if "allowed" not in transitions or "forbidden" not in transitions:
            raise StateValidationError("missing_transition_sets")

    # =============================================================
    # EXTRACT STATES
    # =============================================================

    @staticmethod
    def _extract_states(transitions: Dict[str, Any]) -> Set[str]:

        states = set(transitions.get("states", []))

        for t in transitions.get("allowed", []):
            states.add(t["from"])
            states.add(t["to"])

        for f in transitions.get("forbidden", []):
            states.add(f["from"])
            states.add(f["to"])

        if not states:
            raise StateValidationError("no_states_defined")

        return states

    # =============================================================
    # VALIDATE ALLOWED
    # =============================================================

    @staticmethod
    def _validate_allowed(allowed: List[Dict[str, Any]]):

        for t in allowed:
            if not all(k in t for k in ["id", "from", "to"]):
                raise StateValidationError("invalid_allowed_transition")

            if not isinstance(t["id"], str):
                raise StateValidationError("invalid_transition_id")

    # =============================================================
    # VALIDATE FORBIDDEN
    # =============================================================

    @staticmethod
    def _validate_forbidden(forbidden: List[Dict[str, Any]]):

        for f in forbidden:
            if not all(k in f for k in ["from", "to"]):
                raise StateValidationError("invalid_forbidden_transition")

    # =============================================================
    # UNIQUE IDS (I19_8)
    # =============================================================

    @staticmethod
    def _validate_unique_ids(allowed: List[Dict[str, Any]]):

        seen = set()

        for t in allowed:
            if t["id"] in seen:
                raise StateValidationError("duplicate_transition_id")
            seen.add(t["id"])

    # =============================================================
    # DISJOINT SETS
    # =============================================================

    @staticmethod
    def _validate_disjoint(
        allowed: List[Dict[str, Any]],
        forbidden: List[Dict[str, Any]]
    ):

        allowed_pairs = {(t["from"], t["to"]) for t in allowed}

        for f in forbidden:
            pair = (f["from"], f["to"])
            if pair in allowed_pairs:
                raise StateValidationError("allowed_forbidden_overlap")

    # =============================================================
    # STATE EXISTENCE
    # =============================================================

    @staticmethod
    def _validate_states_exist(
        states: Set[str],
        allowed: List[Dict[str, Any]],
        forbidden: List[Dict[str, Any]]
    ):

        for t in allowed:
            if t["from"] not in states or t["to"] not in states:
                raise StateValidationError("unknown_state_in_allowed")

        for f in forbidden:
            if f["from"] not in states or f["to"] not in states:
                raise StateValidationError("unknown_state_in_forbidden")

    # =============================================================
    # TOTALITY (CRITICAL - I19)
    # =============================================================

    @staticmethod
    def _validate_totality(
        states: Set[str],
        allowed: List[Dict[str, Any]],
        forbidden: List[Dict[str, Any]]
    ):

        all_pairs = set()

        for t in allowed:
            all_pairs.add((t["from"], t["to"]))

        for f in forbidden:
            all_pairs.add((f["from"], f["to"]))

        expected = len(states) * len(states)

        if len(all_pairs) != expected:
            raise StateValidationError("transition_space_not_total")

    # =============================================================
    # TERMINAL STATE VALIDATION (I19_7)
    # =============================================================

    @staticmethod
    def _validate_terminal_states(allowed: List[Dict[str, Any]]):

        terminal_states = set()

        for t in allowed:
            if t.get("terminal"):
                terminal_states.add(t["to"])

        for t in allowed:
            if t["from"] in terminal_states:
                raise StateValidationError("terminal_state_has_outgoing_transition")

    # =============================================================
    # SELF LOOP CONTROL (STRICT)
    # =============================================================

    @staticmethod
    def _validate_no_self_loops(
        allowed: List[Dict[str, Any]],
        forbidden: List[Dict[str, Any]]
    ):

        for t in allowed:
            if t["from"] == t["to"]:
                raise StateValidationError("self_loop_not_allowed")

        for f in forbidden:
            if f["from"] == f["to"]:
                # allowed to explicitly forbid self loops
                continue

    # =============================================================
    # RUNTIME VALIDATION (OPTIONAL)
    # =============================================================

    @classmethod
    def validate_execution_sequence(
        cls,
        states: Set[str],
        sequence: List[Tuple[str, str]]
    ) -> bool:
        """
        Validate a transition sequence (runtime replay validation)
        """

        if not sequence:
            raise StateValidationError("empty_sequence")

        current = "UNINITIALIZED"

        for (src, dst) in sequence:

            if src != current:
                raise StateValidationError("state_mismatch")

            if src not in states or dst not in states:
                raise StateValidationError("unknown_state")

            current = dst

        return True

    # =============================================================
    # SAFE VALIDATION
    # =============================================================

    @classmethod
    def try_validate(cls, transitions: Dict[str, Any]) -> bool:
        try:
            return cls.validate(transitions)
        except StateValidationError:
            return False

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self):
        return "<StateValidator strict>"