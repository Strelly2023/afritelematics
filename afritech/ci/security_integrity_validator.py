from __future__ import annotations

import sys
from typing import Any

from afritech.security.adversarial_engine import AdversarialEngine
from afritech.security.event_authenticator import EventAuthenticator
from afritech.security.integrity_trace import IntegrityTrace
from afritech.security.mutation_guard import MutationGuard
from afritech.simulation.validation_receipt import build_validation_receipt

# afritech.ci.security_integrity_validator
def validate_security(trace: tuple[dict[str, Any], ...]) -> None:
    guard = MutationGuard()
    for event in trace:
        guard.require_valid(event)


def build_receipt():
    auth = EventAuthenticator()
    engine = AdversarialEngine(
        auth,
        MutationGuard(),
        secret="secret",
        trusted_lineage_roots={"known-root"},
    )
    event = {
        "id": "e1",
        "timestamp": 1000,
        "payload": {"status": "requested", "ride_id": "ride-1"},
        "lineage": ("known-root",),
    }
    signature = auth.generate_signature(event, "secret")
    validate_security((event,))
    admitted = engine.process(event, signature)

    _assert_rejects_tampered_payload(auth, engine)
    _assert_rejects_invalid_lineage(auth)
    _assert_rejects_replay(auth)
    _assert_rejects_authority_injection()

    return build_validation_receipt(
        surface="afritech.security.adversarial_engine",
        validator="afritech.ci.security_integrity_validator",
        inputs={"event": event, "signature": signature},
        outputs={
            "integrity_hash": admitted["integrity_hash"],
            "security_trace_hash": IntegrityTrace.hash_event(admitted["security_trace"]),
        },
        trace=admitted,
        evidence=(
            "authenticated_mutation_trace",
            "payload_tamper_rejection_trace",
            "lineage_rejection_trace",
            "replay_mutation_rejection_trace",
            "authority_injection_rejection_trace",
        ),
    )


def _assert_rejects_tampered_payload(
    auth: EventAuthenticator,
    engine: AdversarialEngine,
) -> None:
    event = {
        "id": "e2",
        "timestamp": 1001,
        "payload": {"status": "requested"},
        "lineage": ("known-root",),
    }
    signature = auth.generate_signature(event, "secret")
    event["payload"] = {"status": "completed"}
    try:
        engine.process(event, signature)
    except ValueError:
        return
    raise RuntimeError("Security integrity admitted tampered payload")


def _assert_rejects_invalid_lineage(auth: EventAuthenticator) -> None:
    engine = AdversarialEngine(
        auth,
        MutationGuard(),
        secret="secret",
        trusted_lineage_roots={"known-root"},
    )
    event = {
        "id": "e3",
        "timestamp": 1002,
        "payload": {"status": "requested"},
        "lineage": ("forged-root",),
    }
    signature = auth.generate_signature(event, "secret")
    try:
        engine.process(event, signature)
    except ValueError:
        return
    raise RuntimeError("Security integrity admitted invalid lineage")


def _assert_rejects_replay(auth: EventAuthenticator) -> None:
    engine = AdversarialEngine(auth, MutationGuard(), secret="secret")
    event = {"id": "e4", "timestamp": 1003, "payload": {"status": "requested"}}
    signature = auth.generate_signature(event, "secret")
    engine.process(event, signature)
    try:
        engine.process(event, signature)
    except ValueError:
        return
    raise RuntimeError("Security integrity admitted replay mutation")


def _assert_rejects_authority_injection() -> None:
    event = {
        "id": "e5",
        "timestamp": 1004,
        "payload": {"metadata": {"mutation_witness": "forged"}},
    }
    try:
        MutationGuard().require_valid(event)
    except ValueError:
        return
    raise RuntimeError("Security integrity admitted authority injection")


def run() -> None:
    receipt = build_receipt()
    if not receipt.deterministic or not receipt.replay_safe:
        raise RuntimeError("Security integrity receipt is not replay safe")
    print("Security integrity validation PASSED")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"Security integrity validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
