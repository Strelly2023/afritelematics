# afritech/tests/test_state_machine.py

import pytest
from afritech.constitution.state_machine import (
    ConstitutionalStateMachine,
    State,
    Event,
    StateError
)


def test_valid_transition():
    sm = ConstitutionalStateMachine()

    state = State.SEALED
    state = sm.transition(state, Event.SUBMIT_ADR)

    assert state == State.PROPOSAL_PENDING


def test_illegal_transition():
    sm = ConstitutionalStateMachine()

    with pytest.raises(StateError):
        sm.transition(State.SEALED, Event.APPROVE)


def test_no_rollback():
    sm = ConstitutionalStateMachine()

    state = sm.transition(State.SEALED, Event.SUBMIT_ADR)
    state = sm.transition(state, Event.APPROVE)

    with pytest.raises(StateError):
        sm.transition(state, Event.SUBMIT_ADR)
