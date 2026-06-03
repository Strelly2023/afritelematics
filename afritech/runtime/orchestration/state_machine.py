"""
AfriTech State Machine

PURPOSE:
--------
Manages deterministic state transitions for workflows.

Responsibilities:
- track current state
- enforce valid transitions
- provide replay-safe state evolution
- prevent invalid state mutations

CRITICAL LAW:
-------------
State Machine MAY:
- transition state
- validate transitions

State Machine may NOT:
- modify event payload
- introduce randomness
- violate deterministic execution
"""

# ============================================================
# ✅ STATE MACHINE CLASS
# ============================================================

class StateMachine:
    """
    Deterministic state machine for workflow execution.
    """

    def __init__(self, initial_state="init", transitions=None):
        """
        Initialize state machine.

        Args:
            initial_state: starting state
            transitions: dict defining allowed transitions
        """

        self.state = initial_state

        self.transitions = transitions or {
            "init": {"start": "running"},
            "running": {
                "complete": "done",
                "fail": "error",
            },
            "error": {
                "retry": "running",
                "abort": "terminated",
            },
            "done": {},
            "terminated": {},
        }

    # ========================================================
    # ✅ TRANSITION STATE
    # ========================================================

    def transition(self, event_type: str):
        """
        Perform a state transition based on event.

        Returns:
            new state
        """

        if event_type not in self.transitions.get(self.state, {}):
            raise Exception(
                f"[STATE ERROR] Invalid transition: {self.state} → {event_type}"
            )

        new_state = self.transitions[self.state][event_type]
        self.state = new_state

        return self.state

    # ========================================================
    # ✅ GET CURRENT STATE
    # ========================================================

    def get_state(self):
        """
        Returns current state.
        """

        return self.state

    # ========================================================
    # ✅ VALIDATE TRANSITION (NO MUTATION)
    # ========================================================

    def can_transition(self, event_type: str):
        """
        Check if transition is allowed without applying it.
        """

        return event_type in self.transitions.get(self.state, {})

    # ========================================================
    # ✅ RESET STATE MACHINE
    # ========================================================

    def reset(self, state="init"):
        """
        Reset to initial or specified state.
        """

        self.state = state

    # ========================================================
    # ✅ VALIDATE STRUCTURE
    # ============================================================

    def validate(self):
        """
        Ensure transition map is valid.
        """

        if not isinstance(self.transitions, dict):
            raise Exception("[STATE ERROR] Invalid transitions structure")

        for state, mapping in self.transitions.items():
            if not isinstance(mapping, dict):
                raise Exception(
                    f"[STATE ERROR] Invalid mapping for state: {state}"
                )

        return True

    # ========================================================
    # ✅ TERMINAL STATE CHECK
    # ============================================================

    def is_terminal(self):
        """
        Check if current state is terminal.
        """

        return len(self.transitions.get(self.state, {})) == 0

    # ========================================================
    # ✅ AVAILABLE TRANSITIONS
    # ============================================================

    def available_transitions(self):
        """
        Returns possible events from current state.
        """

        return list(self.transitions.get(self.state, {}).keys())

    # ========================================================
    # ✅ DETERMINISM CHECK
    # ============================================================

    def validate_determinism(self):
        """
        Ensure transitions are deterministic.
        """

        for state, mapping in self.transitions.items():
            for event, target in mapping.items():
                if not isinstance(target, str):
                    raise Exception(
                        f"[STATE ERROR] Non-deterministic transition {state}->{event}"
                    )

        return True

    # ========================================================
    # ✅ TRACE STATE EVOLUTION
    # ============================================================

    def trace(self, event_sequence: list):
        """
        Simulate transitions for debugging.

        Does NOT modify actual state.
        """

        temp_state = self.state
        trace = []

        for event in event_sequence:
            if event in self.transitions.get(temp_state, {}):
                next_state = self.transitions[temp_state][event]
            else:
                next_state = "invalid"

            trace.append({
                "from": temp_state,
                "event": event,
                "to": next_state,
            })

            temp_state = next_state if next_state != "invalid" else temp_state

        return trace