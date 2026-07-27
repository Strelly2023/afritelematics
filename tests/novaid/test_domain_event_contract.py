from datetime import datetime
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    IdentityLifecycleEvent,
    IdentityMergedEvent,
    IdentityStatus,
    IdentityVerificationEvent,
    VerificationStatus,
    AssuranceLevel,
)
from afritech.novaid.domain.domain_event_codec import (
    DOMAIN_EVENT_SCHEMA_VERSION,
    encode_domain_event,
)
from afritech.novaid.domain.domain_events import (
    NovaIDDomainEvent,
    domain_event_subject_ids,
)


def uid() -> str:
    return str(uuid4())


def lifecycle_event() -> IdentityLifecycleEvent:
    return IdentityLifecycleEvent(
        event_id=uid(),
        event_type="IDENTITY_ACTIVATED",
        tenant_id=uid(),
        identity_id=uid(),
        actor_identity_id=uid(),
        correlation_id=uid(),
        request_id=uid(),
        previous_status=IdentityStatus.PENDING_VERIFICATION,
        current_status=IdentityStatus.ACTIVE,
        identity_version=2,
    )


def verification_event() -> IdentityVerificationEvent:
    return IdentityVerificationEvent(
        event_id=uid(),
        event_type="IDENTITY_VERIFIED",
        tenant_id=uid(),
        identity_id=uid(),
        actor_identity_id=uid(),
        correlation_id=uid(),
        request_id=uid(),
        previous_status=VerificationStatus.IN_PROGRESS,
        current_status=VerificationStatus.VERIFIED,
        previous_assurance_level=AssuranceLevel.NID_AL0,
        current_assurance_level=AssuranceLevel.NID_AL2,
        identity_version=3,
    )


def merge_event() -> IdentityMergedEvent:
    return IdentityMergedEvent(
        event_id=uid(),
        event_type="IDENTITY_MERGED",
        tenant_id=uid(),
        source_identity_id=uid(),
        target_identity_id=uid(),
        actor_identity_id=uid(),
        correlation_id=uid(),
        request_id=uid(),
        source_version=2,
        target_version=4,
    )


@pytest.mark.parametrize(
    "event_factory",
    (
        lifecycle_event,
        verification_event,
        merge_event,
    ),
)
def test_all_canonical_events_satisfy_protocol(
    event_factory,
) -> None:
    event = event_factory()

    assert isinstance(event, NovaIDDomainEvent)
    assert event.event_id
    assert event.event_type
    assert event.tenant_id
    assert event.actor_identity_id
    assert event.correlation_id
    assert event.request_id
    assert isinstance(event.occurred_at, datetime)


def test_single_identity_event_subject_resolution() -> None:
    event = lifecycle_event()

    assert domain_event_subject_ids(event) == (
        event.identity_id,
    )


def test_merge_event_subject_resolution_is_ordered() -> None:
    event = merge_event()

    assert domain_event_subject_ids(event) == (
        event.source_identity_id,
        event.target_identity_id,
    )


@pytest.mark.parametrize(
    "event_factory",
    (
        lifecycle_event,
        verification_event,
        merge_event,
    ),
)
def test_domain_event_encoding_is_canonical(
    event_factory,
) -> None:
    event = event_factory()
    encoded = encode_domain_event(event)

    assert encoded["schema_version"] == (
        DOMAIN_EVENT_SCHEMA_VERSION
    )
    assert encoded["event_id"] == event.event_id
    assert encoded["event_type"] == event.event_type
    assert encoded["tenant_id"] == event.tenant_id
    assert encoded["actor_identity_id"] == (
        event.actor_identity_id
    )
    assert encoded["correlation_id"] == (
        event.correlation_id
    )
    assert encoded["request_id"] == event.request_id
    assert isinstance(encoded["occurred_at"], str)
    assert isinstance(encoded["payload"], dict)


def test_encoding_converts_enums_and_timestamps() -> None:
    encoded = encode_domain_event(lifecycle_event())
    payload = encoded["payload"]

    assert payload["previous_status"] == (
        "PENDING_VERIFICATION"
    )
    assert payload["current_status"] == "ACTIVE"
    assert isinstance(payload["occurred_at"], str)
