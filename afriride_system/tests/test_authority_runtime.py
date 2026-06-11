from __future__ import annotations

import pytest

from afriride_system.backend.authority_runtime import (
    AuthorityRuntimeError,
    assert_protocol_version_compatible,
    authority_envelope,
    authority_hash,
    compatibility_report,
)


ARCHITECTURE_INVARIANTS = (
    "I3_NO_SILENT_MUTATION",
    "I4_DETERMINISTIC_EXECUTION",
    "I5_REPLAY_REQUIRED",
    "I6_REPLAY_AUTHORITY",
    "I7_TRANSCRIPT_COMPLETENESS",
    "I8_TRANSCRIPT_HASH_STABILITY",
    "I11_AUTHORITY_DECLARATION",
)


def test_authority_envelope_is_hashed_and_registry_validated() -> None:
    payload = authority_envelope(
        doc_id="DOC-ARCH-001",
        doc_version="1.0.0",
        governed_invariants=ARCHITECTURE_INVARIANTS,
        surface="replay_snapshot",
    )

    assert payload["doc_id"] == "DOC-ARCH-001"
    assert payload["doc_version"] == "1.0.0"
    assert payload["surface"] == "replay_snapshot"
    assert payload["authority_hash"] == authority_hash(
        doc_id="DOC-ARCH-001",
        doc_version="1.0.0",
        governed_invariants=ARCHITECTURE_INVARIANTS,
    )
    assert len(payload["authority_hash"]) == 64


def test_authority_envelope_rejects_runtime_version_drift() -> None:
    with pytest.raises(AuthorityRuntimeError, match="authority version mismatch"):
        authority_envelope(
            doc_id="DOC-ARCH-001",
            doc_version="9.9.9",
            governed_invariants=ARCHITECTURE_INVARIANTS,
            surface="replay_snapshot",
        )


def test_authority_envelope_rejects_runtime_invariant_drift() -> None:
    with pytest.raises(AuthorityRuntimeError, match="authority invariant mismatch"):
        authority_envelope(
            doc_id="DOC-ARCH-001",
            doc_version="1.0.0",
            governed_invariants=ARCHITECTURE_INVARIANTS[:-1],
            surface="replay_snapshot",
        )


def test_protocol_compatibility_report_declares_current_version_supported() -> None:
    report = compatibility_report(protocol_version="1.0.0")

    assert report["protocol_version"] == "1.0.0"
    assert report["verifier_version"] == "1.0.0"
    assert report["supported"] is True
    assert report["status"] == "CURRENT"


def test_protocol_compatibility_rejects_breaking_version() -> None:
    with pytest.raises(AuthorityRuntimeError, match="protocol version incompatible with verifier"):
        assert_protocol_version_compatible(protocol_version="2.0.0")
