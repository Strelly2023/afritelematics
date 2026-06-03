from __future__ import annotations

import pytest

from afritech.security.adversarial_engine import AdversarialEngine
from afritech.security.event_authenticator import EventAuthenticator
from afritech.security.mutation_guard import MutationGuard


def test_invalid_structure() -> None:
    guard = MutationGuard()

    assert not guard.validate({"id": "e1"})


def test_reject_nested_authority_injection() -> None:
    guard = MutationGuard()

    event = {
        "id": "e1",
        "timestamp": 1000,
        "payload": {"metadata": {"witness_hash": "forged"}},
    }

    with pytest.raises(ValueError, match="Forbidden authority field"):
        guard.require_valid(event)


def test_replay_mutation_is_rejected() -> None:
    auth = EventAuthenticator()
    engine = AdversarialEngine(auth, MutationGuard(), secret="secret")
    event = {"id": "e1", "timestamp": 1000, "payload": {"status": "requested"}}
    signature = auth.generate_signature(event, "secret")

    engine.process(event, signature)

    with pytest.raises(ValueError, match="Replay mutation detected"):
        engine.process(event, signature)
