# afritech/constitution/state_machine.py

"""
Constitutional State Machine

Defines legal transitions of system state.
Enforces:
- no illegal mutation
- no rollback
- explicit transition law
"""

from typing import Dict


class StateError(Exception):
    pass


class State:
    SEALED = "SEALED"
    PROPOSAL_PENDING = "PROPOSAL_PENDING"
    ADR_APPROVED = "ADR_APPROVED"
    EPOCH_ADVANCING = "EPOCH_ADVANCING"
    RESEALED = "RESEALED"
    INVALID = "INVALID"


class Event:
    SUBMIT_ADR = "submit_adr"
    APPROVE = "approve"
    ADVANCE_EPOCH = "advance_epoch"
    RESEAL = "reseal"
    REJECT = "reject"


TRANSITIONS = {
    State.SEALED: {
        Event.SUBMIT_ADR: State.PROPOSAL_PENDING,
    },
    State.PROPOSAL_PENDING: {
        Event.APPROVE: State.ADR_APPROVED,
        Event.REJECT: State.SEALED,
    },
    State.ADR_APPROVED: {
        Event.ADVANCE_EPOCH: State.EPOCH_ADVANCING,
    },
    State.EPOCH_ADVANCING: {
        Event.RESEAL: State.RESEALED,
    },
    State.RESEALED: {},  # terminal before next cycle
}


class ConstitutionalStateMachine:

    def transition(self, current: str, event: str) -> str:
        if current not in TRANSITIONS:
            raise StateError(f"invalid_state: {current}")

        allowed = TRANSITIONS[current]

        if event not in allowed:
            raise StateError(
                f"illegal_transition: {current} → {event}"
            )

        next_state = allowed[event]

        if next_state == State.INVALID:
            raise StateError("transition_to_invalid_state")

        return next_state