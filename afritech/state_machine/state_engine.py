# afritech/state_machine/state_engine.py

"""
AfriTech State Engine

Purpose:
Enforce deterministic, total, and replay-safe state transitions.

Responsibilities:
- enforce allowed transitions
- reject forbidden or undefined transitions
- maintain transition chain (hash-linked)
- support replay and verification
- integrate with trace + proof systems

This is the EXECUTION SEMANTICS layer of the system.
"""

from typing import Dict, Any, List, Optional

from afritech.state_machine.state_hash import (
    hash_transition,
    hash_transition_record,
    hash_transition_sequence,
    validate_transition_sequence,
)


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class StateEngineError(Exception):
    """Raised when state transition fails"""
    pass


# -----------------------------------------------------------------
# ENGINE
# -----------------------------------------------------------------

class StateEngine:

    def __init__(self, transitions: Dict[str, Any]):

        self.allowed = transitions.get("allowed", [])
        self.forbidden = transitions.get("forbidden", [])
        self.states = transitions.get("states", [])

        self.current_state: str = "UNINITIALIZED"
        self.history: List[Dict[str, Any]] = []

        self._validate_transitions()
        self._finalized = False

    # -----------------------------------------------------------------
    # VALIDATION AT INIT
    # -----------------------------------------------------------------

    def _validate_transitions(self):

        if not self.allowed:
            raise StateEngineError("missing_allowed_transitions")

        allowed_pairs = set()

        for t in self.allowed:
            key = (t["from"], t["to"])
            if key in allowed_pairs:
                raise StateEngineError("duplicate_allowed_transition")
            allowed_pairs.add(key)

        # Disallow overlap with forbidden
        for f in self.forbidden:
            if (f["from"], f["to"]) in allowed_pairs:
                raise StateEngineError("conflicting_transition")

    # -----------------------------------------------------------------
    # TRANSITION EXECUTION
    # -----------------------------------------------------------------

    def transition(self, target_state: str) -> Dict[str, Any]:

        if self._finalized:
            raise StateEngineError("state_machine_finalized")

        current = self.current_state

        # ---------------------------------------------------------
        # TERMINAL STATE CHECK
        # ---------------------------------------------------------

        if current in ["COMPLETED", "FAILED"]:
            raise StateEngineError("terminal_state_reached")

        # ---------------------------------------------------------
        # FORBIDDEN CHECK
        # ---------------------------------------------------------

        for f in self.forbidden:
            if f["from"] == current and f["to"] == target_state:
                raise StateEngineError("forbidden_transition")

        # ---------------------------------------------------------
        # FIND ALLOWED
        # ---------------------------------------------------------

        transition_def: Optional[Dict[str, Any]] = None

        for t in self.allowed:
            if t["from"] == current and t["to"] == target_state:
                transition_def = t
                break

        if not transition_def:
            raise StateEngineError("unauthorized_transition")

        # ---------------------------------------------------------
        # BUILD RECORD
        # ---------------------------------------------------------

        index = len(self.history)
        previous_hash = (
            self.history[-1]["transition_hash"]
            if self.history
            else "GENESIS"
        )

        base_transition = {
            "id": transition_def["id"],
            "from": current,
            "to": target_state,
        }

        transition_hash = hash_transition(base_transition)

        record = {
            "index": index,
            "id": transition_def["id"],
            "from": current,
            "to": target_state,
            "previous_hash": previous_hash,
            "transition_hash": transition_hash,
        }

        # Optional stronger chaining
        record["record_hash"] = hash_transition_record(record)

        # ---------------------------------------------------------
        # COMMIT
        # ---------------------------------------------------------

        self.history.append(record)
        self.current_state = target_state

        # Auto-finalize if terminal
        if target_state in ["COMPLETED", "FAILED"]:
            self._finalized = True

        return record

    # -----------------------------------------------------------------
    # GET STATE
    # -----------------------------------------------------------------

    def get_state(self) -> str:
        return self.current_state

    # -----------------------------------------------------------------
    # HISTORY ACCESS
    # -----------------------------------------------------------------

    def get_history(self) -> List[Dict[str, Any]]:
        return self.history

    # -----------------------------------------------------------------
    # REPLAY
    # -----------------------------------------------------------------

    def replay(self, sequence: List[Dict[str, Any]]) -> str:
        """
        Replay sequence deterministically
        """

        self.reset()

        for record in sequence:
            self.transition(record["to"])

        return self.current_state

    # -----------------------------------------------------------------
    # VERIFY HISTORY (CRITICAL)
    # -----------------------------------------------------------------

    def verify_history(self) -> bool:
        """
        Ensure full integrity of transition chain
        """

        try:
            validate_transition_sequence(self.history)
            return True
        except Exception:
            return False

    # -----------------------------------------------------------------
    # SNAPSHOT HASH
    # -----------------------------------------------------------------

    def snapshot_hash(self) -> str:
        """
        Compute hash of current state snapshot
        """

        from afritech.state_machine.state_hash import hash_state_snapshot

        return hash_state_snapshot(
            self.current_state,
            self.history
        )

    # -----------------------------------------------------------------
    # REPLAY HASH
    # -----------------------------------------------------------------

    def replay_commitment(self) -> str:
        """
        Final commitment hash (state + path)
        """

        from afritech.state_machine.state_hash import compute_replay_hash

        return compute_replay_hash(
            self.current_state,
            self.history
        )

    # -----------------------------------------------------------------
    # RESET ENGINE
    # -----------------------------------------------------------------

    def reset(self):

        self.current_state = "UNINITIALIZED"
        self.history = []
        self._finalized = False

    # -----------------------------------------------------------------
    # EXPORT
    # -----------------------------------------------------------------

    def export(self) -> Dict[str, Any]:
        """
        Export full state machine snapshot
        """

        return {
            "current_state": self.current_state,
            "history": self.history,
            "snapshot_hash": self.snapshot_hash(),
            "replay_commitment": self.replay_commitment(),
        }

    # -----------------------------------------------------------------
    # IMPORT
    # -----------------------------------------------------------------

    def load(self, data: Dict[str, Any]):
        """
        Load state machine snapshot (validated)
        """

        if "history" not in data or "current_state" not in data:
            raise StateEngineError("invalid_snapshot")

        self.history = data["history"]
        self.current_state = data["current_state"]

        if not self.verify_history():
            raise StateEngineError("invalid_history_chain")

    # -----------------------------------------------------------------
    # DEBUG
    # -----------------------------------------------------------------

    def __repr__(self):
        return (
            f"<StateEngine state={self.current_state} "
            f"steps={len(self.history)} "
            f"finalized={self._finalized}>"
        )