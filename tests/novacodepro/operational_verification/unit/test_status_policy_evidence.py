import pytest

from afritech.novacodepro.operational_verification.enums import CapabilityState, EvidenceStatus
from afritech.novacodepro.operational_verification.errors import EvidencePolicyError, InvalidTransitionError
from afritech.novacodepro.operational_verification.evidence import create_evidence_envelope, validate_evidence
from afritech.novacodepro.operational_verification.policy import assert_transition_allowed
from afritech.novacodepro.operational_verification.status import invariant_status


def test_valid_and_skipped_transitions() -> None:
    assert_transition_allowed(CapabilityState.CONFIGURED, CapabilityState.RUNNING)
    assert_transition_allowed(CapabilityState.RUNNING, CapabilityState.EXECUTED)
    with pytest.raises(InvalidTransitionError):
        assert_transition_allowed(CapabilityState.CONFIGURED, CapabilityState.VERIFIED)
    with pytest.raises(InvalidTransitionError):
        assert_transition_allowed(CapabilityState.EXECUTED, CapabilityState.APPROVED)
    with pytest.raises(InvalidTransitionError):
        assert_transition_allowed(CapabilityState.APPROVAL_PENDING, CapabilityState.APPROVED, actor_type="CLIENT_REQUEST")


def test_evidence_envelope_is_signed_and_development_signature_blocks_production() -> None:
    evidence = create_evidence_envelope("accessibility", "test", "ci", "portal", "rel-1", "run-1")
    body = evidence.to_dict()

    assert body["checksum"].startswith("sha256:")
    assert body["signature"].startswith("sha256:")
    with pytest.raises(EvidencePolicyError):
        validate_evidence(evidence, production=True)


def test_expired_and_superseded_evidence_rejected() -> None:
    evidence = create_evidence_envelope("visual", "test", "ci", "portal", "rel-1", "run-1")
    evidence.status = EvidenceStatus.SUPERSEDED

    with pytest.raises(EvidencePolicyError):
        validate_evidence(evidence)


def test_invariants_fail_closed() -> None:
    status = invariant_status()

    assert status["GA_ALLOWED"] is False
    assert status["REAL_PAYMENTS_ENABLED"] is False
    assert status["NOVA_AI_AUTHORITY"] == "ADVISORY_ONLY"
