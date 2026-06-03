from __future__ import annotations

import pytest

from afritech.security.adversarial_engine import AdversarialEngine
from afritech.security.event_authenticator import EventAuthenticator
from afritech.security.mutation_guard import MutationGuard


# ============================================================
# FIXTURE
# ============================================================

def _engine() -> AdversarialEngine:
    return AdversarialEngine(
        EventAuthenticator(),
        MutationGuard(),
        secret="secret",
        trusted_lineage_roots={"known-root"},
    )


def _event(lineage=("known-root",)):
    return {
        "id": "e1",
        "timestamp": 1000,
        "payload": {"status": "requested"},
        "lineage": lineage,
    }


# ============================================================
# TESTS
# ============================================================

def test_reject_invalid_signature() -> None:
    engine = _engine()

    with pytest.raises(ValueError, match="Authentication failed"):
        engine.process(_event(), "fake")


def test_authenticated_event_is_admitted_with_security_trace() -> None:
    auth = EventAuthenticator()
    engine = _engine()

    event = _event()
    signature = auth.generate_signature(event, "secret")

    admitted = engine.process(event, signature)

    # ✅ integrity hash exists and is sha256
    assert admitted["integrity_hash"]
    assert len(admitted["integrity_hash"]) == 64

    # ✅ security trace structure
    trace = admitted["security_trace"]

    assert isinstance(trace, dict)
    assert "stages" in trace

    # ✅ deterministic stage sequence
    assert trace["stages"] == [
        "authenticity",
        "structure",
        "lineage",
        "admissibility",
    ]


def test_reject_untrusted_lineage() -> None:
    auth = EventAuthenticator()
    engine = _engine()

    event = _event(lineage=("forged-root",))
    signature = auth.generate_signature(event, "secret")

    with pytest.raises(ValueError, match="Lineage validation failed"):
        engine.process(event, signature)


# ============================================================
# REPLAY PROTECTION TEST ✅
# ============================================================

def test_engine_rejects_replay() -> None:
    auth = EventAuthenticator()
    engine = _engine()

    event = _event()
    signature = auth.generate_signature(event, "secret")

    engine.process(event, signature)

    # ✅ second call must be rejected
    with pytest.raises(ValueError, match="Replay mutation detected"):
        engine.process(event, signature)


# ============================================================
# DETERMINISM TEST ✅ FIXED
# ============================================================

def test_adversarial_engine_is_deterministic_for_same_input() -> None:
    auth = EventAuthenticator()

    # ✅ use separate engines (no replay memory)
    engine_a = _engine()
    engine_b = _engine()

    event = _event()
    signature = auth.generate_signature(event, "secret")

    a = engine_a.process(event, signature)
    b = engine_b.process(event, signature)

    assert a["integrity_hash"] == b["integrity_hash"]
    assert a["security_trace"] == b["security_trace"]