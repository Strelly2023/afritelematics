from __future__ import annotations

import json
from copy import deepcopy

import pytest

from afritech.identity.mobility_participant import (
    AUTHORITY_BOUNDARY,
    SCHEMA,
    MobilityParticipant,
    MobilityParticipantError,
    validate_mobility_participant,
)


def _sample_payload() -> dict[str, object]:
    return {
        "participant_id": "mp-001",
        "display_name": "Amina Operator",
        "roles": ["driver", "courier"],
        "verification_status": "verified",
        "trust_score": 92.5,
        "evidence_links": ["evt-001", "evt-002"],
        "metadata": {"city": "Melbourne"},
    }


def test_mobility_participant_happy_path():
    participant = MobilityParticipant.from_mapping(_sample_payload())

    assert participant.participant_id == "mp-001"
    assert participant.multi_role is True
    assert participant.canonical_dict()["schema"] == SCHEMA


def test_mobility_participant_rejects_invalid_role():
    payload = _sample_payload()
    payload["roles"] = ["driver", "pilot"]

    with pytest.raises(MobilityParticipantError):
        MobilityParticipant.from_mapping(payload)


def test_mobility_participant_is_deterministic():
    a = MobilityParticipant.from_mapping(_sample_payload())
    b = MobilityParticipant.from_mapping(_sample_payload())

    assert a == b
    assert a.participant_hash() == b.participant_hash()


def test_mobility_participant_replay_stability():
    participant = MobilityParticipant.from_mapping(_sample_payload())

    assert participant.canonical_dict() == deepcopy(participant).canonical_dict()


def test_mobility_participant_tampering_detection():
    participant = MobilityParticipant.from_mapping(_sample_payload())
    tampered = deepcopy(participant.canonical_dict())
    tampered["trust_score"] = 0.0

    assert tampered != participant.canonical_dict()


def test_mobility_participant_serialization_roundtrip():
    participant = MobilityParticipant.from_mapping(_sample_payload())

    encoded = json.dumps(participant.canonical_dict(), sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded["participant_id"] == "mp-001"
    assert decoded["roles"] == ["courier", "driver"]


def test_mobility_participant_schema_integrity():
    participant = MobilityParticipant.from_mapping(_sample_payload())

    assert participant.canonical_dict()["schema"] == SCHEMA


def test_mobility_participant_authority_boundary():
    participant = MobilityParticipant.from_mapping(_sample_payload())

    assert participant.canonical_dict()["authority_boundary"] == AUTHORITY_BOUNDARY
    assert participant.canonical_dict()["identity_is_truth_authority"] is False


def test_mobility_participant_governance_constraints():
    participant = MobilityParticipant.from_mapping(_sample_payload())
    data = participant.canonical_dict()

    assert data["identity_is_reference_only"] is True
    assert data["identity_overrides_replay"] is False
    assert data["identity_overrides_proof"] is False
    assert data["identity_overrides_payment"] is False


def test_mobility_participant_backward_compatibility():
    participant = MobilityParticipant.from_mapping(_sample_payload())
    modified = deepcopy(participant.canonical_dict())
    modified.pop("metadata", None)

    assert modified["participant_id"] == "mp-001"


def test_mobility_participant_detects_drift():
    participant = MobilityParticipant.from_mapping(_sample_payload())
    tampered = deepcopy(participant.canonical_dict())
    tampered["roles"] = ["driver"]

    assert tampered != participant.canonical_dict()


def test_mobility_participant_reproducibility_under_load():
    hashes = {
        MobilityParticipant.from_mapping(_sample_payload()).participant_hash()
        for _ in range(5)
    }

    assert len(hashes) == 1


def test_validate_mobility_participant_accepts_model():
    participant = MobilityParticipant.from_mapping(_sample_payload())

    assert validate_mobility_participant(participant) is participant


def test_validate_mobility_participant_rejects_invalid_input():
    with pytest.raises(MobilityParticipantError):
        validate_mobility_participant(None)  # type: ignore[arg-type]


def test_mobility_participant_normalizes_evidence_links():
    payload = _sample_payload()
    payload["evidence_links"] = ["evt-002", "evt-001", "evt-001"]

    participant = MobilityParticipant.from_mapping(payload)

    assert participant.evidence_links == ("evt-001", "evt-002")
