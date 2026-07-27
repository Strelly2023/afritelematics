from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from afritech.novaid.domain import (
    AddressType,
    AssuranceLevel,
    ContactPoint,
    ContactPointType,
    Identity,
    IdentityAddress,
    IdentityIdentifier,
    IdentityName,
    IdentityStatus,
    IdentityType,
    IdentifierType,
    LegalName,
    NameType,
    VerificationStatus,
)


def test_existing_positional_identity_constructor_remains_compatible() -> None:
    identity = Identity(
        "00000000-0000-0000-0000-000000000001",
        "00000000-0000-0000-0000-000000000002",
        "person@example.com",
    )

    assert identity.status is IdentityStatus.PENDING_VERIFICATION
    assert identity.identity_type is IdentityType.PERSON
    assert identity.verification_status is VerificationStatus.UNVERIFIED
    assert identity.assurance_level is AssuranceLevel.NID_AL0
    assert identity.alternative_names == ()
    assert identity.contact_points == ()
    assert identity.addresses == ()
    assert identity.identifiers == ()
    assert identity.metadata == {}


def test_canonical_person_identity_accepts_immutable_profile_values() -> None:
    legal_name = LegalName(
        given_names=("Djuma",),
        middle_names=("Example",),
        family_name="Kikombe",
    )

    identity = Identity(
        identity_id="00000000-0000-0000-0000-000000000011",
        tenant_id="00000000-0000-0000-0000-000000000012",
        normalized_email="djuma@example.com",
        legal_name=legal_name,
        preferred_name="Djuma",
        alternative_names=(
            IdentityName(
                name_type=NameType.PREFERRED,
                display_name="Djuma",
            ),
        ),
        contact_points=(
            ContactPoint(
                contact_type=ContactPointType.EMAIL,
                value="djuma@example.com",
                verified=True,
                primary=True,
            ),
        ),
        addresses=(
            IdentityAddress(
                address_type=AddressType.RESIDENTIAL,
                line1="1 Example Street",
                locality="Melbourne",
                country_code="au",
                region="VIC",
                postal_code="3000",
            ),
        ),
        identifiers=(
            IdentityIdentifier(
                identifier_type=IdentifierType.NOVAID,
                value="nid-example",
                issuer="NovaID",
                primary=True,
            ),
        ),
        verification_status=VerificationStatus.VERIFIED,
        assurance_level=AssuranceLevel.NID_AL2,
        metadata={"source": "canonical-aggregate-test"},
    )

    assert identity.legal_name is legal_name
    assert identity.addresses[0].country_code == "AU"
    assert identity.assurance_level is AssuranceLevel.NID_AL2


def test_lifecycle_transition_preserves_canonical_profile() -> None:
    identity = Identity(
        identity_id="00000000-0000-0000-0000-000000000021",
        tenant_id="00000000-0000-0000-0000-000000000022",
        normalized_email="transition@example.com",
        legal_name=LegalName(
            given_names=("Canonical",),
            family_name="Identity",
        ),
    )

    transitioned = identity.transition(IdentityStatus.ACTIVE)

    assert transitioned.status is IdentityStatus.ACTIVE
    assert transitioned.version == identity.version + 1
    assert transitioned.legal_name == identity.legal_name
    assert transitioned.identity_type is IdentityType.PERSON


def test_canonical_value_objects_are_frozen() -> None:
    legal_name = LegalName(
        given_names=("Immutable",),
        family_name="Person",
    )

    with pytest.raises(FrozenInstanceError):
        legal_name.family_name = "Changed"  # type: ignore[misc]


def test_invalid_canonical_values_fail_closed() -> None:
    with pytest.raises(ValueError, match="LEGAL_FAMILY_NAME_REQUIRED"):
        LegalName(given_names=("Person",), family_name="")

    with pytest.raises(ValueError, match="INVALID_COUNTRY_CODE"):
        IdentityAddress(
            address_type=AddressType.RESIDENTIAL,
            line1="1 Example Street",
            locality="Melbourne",
            country_code="Australia",
        )

    now = datetime.now(UTC)

    with pytest.raises(ValueError, match="INVALID_IDENTIFIER_PERIOD"):
        IdentityIdentifier(
            identifier_type=IdentifierType.PASSPORT_NUMBER,
            value="P123456",
            valid_from=now,
            valid_until=now,
        )
