from enum import Enum


class RideStatus(str, Enum):
    """
    Strongly-typed ride states.

    Inherits from str for:
    - JSON serialization compatibility
    - clean comparison with payload values
    """

    REQUESTED = "REQUESTED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class RideState:
    """
    Authoritative Ride State Machine

    Guarantees:
    - Strict lifecycle transitions
    - Deterministic execution
    - Centralized state rules
    """

    # -----------------------------
    # VALID TRANSITIONS
    # -----------------------------
    VALID_TRANSITIONS = {
        RideStatus.REQUESTED: {RideStatus.ASSIGNED},
        RideStatus.ASSIGNED: {RideStatus.IN_PROGRESS},
        RideStatus.IN_PROGRESS: {RideStatus.COMPLETED},
        RideStatus.COMPLETED: set(),  # terminal
    }

    # -----------------------------
    # TRANSITION VALIDATION
    # -----------------------------
    @classmethod
    def transition(cls, current_state, next_state):
        """
        Validate and apply a state transition.

        Raises:
            Exception if transition is invalid
        """

        if current_state is None:
            raise Exception("Cannot transition from None state")

        # Normalize to enum (handles raw string input safely)
        current_state = cls._normalize(current_state)
        next_state = cls._normalize(next_state)

        allowed = cls.VALID_TRANSITIONS.get(current_state, set())

        if next_state not in allowed:
            raise Exception(
                f"Invalid transition {current_state.value} → {next_state.value}"
            )

        return next_state

    # -----------------------------
    # NORMALIZATION
    # -----------------------------
    @classmethod
    def _normalize(cls, state):
        """
        Accept both Enum and raw string.

        Ensures internal consistency.
        """

        if isinstance(state, RideStatus):
            return state

        try:
            return RideStatus(state)
        except ValueError:
            raise Exception(f"Invalid state value: {state}")

    # -----------------------------
    # VALIDATION HELPERS
    # -----------------------------
    @classmethod
    def is_terminal(cls, state):
        state = cls._normalize(state)
        return state == RideStatus.COMPLETED

    @classmethod
    def is_active(cls, state):
        state = cls._normalize(state)
        return state in {
            RideStatus.REQUESTED,
            RideStatus.ASSIGNED,
            RideStatus.IN_PROGRESS,
        }

    @classmethod
    def can_transition(cls, current_state, next_state):
        """
        Safe check without raising exception.
        """

        try:
            current_state = cls._normalize(current_state)
            next_state = cls._normalize(next_state)

            return next_state in cls.VALID_TRANSITIONS.get(current_state, set())
        except Exception:
            return False

    @classmethod
    def list_allowed(cls, current_state):
        """
        Returns allowed next states.
        Useful for debugging / UI hints.
        """

        current_state = cls._normalize(current_state)

        return list(cls.VALID_TRANSITIONS.get(current_state, set()))

    # -----------------------------
    # DEBUG
    # -----------------------------
    @classmethod
    def all_states(cls):
        return list(RideStatus)