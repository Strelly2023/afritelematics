from datetime import UTC, datetime
from uuid import uuid4

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
    IdentityType,
    IdentifierType,
    LegalName,
    NameType,
    RequestContext,
    VerificationStatus,
)
from afritech.novaid.persistence import NovaIDUnitOfWork


def uid() -> str:
    return str(uuid4())


def test_sqlite_canonical_identity_round_trip() -> None:
    tenant_id = uid()
    identity_id = uid()
    now = datetime.now(UTC)

    identity = Identity(
        identity_id=identity_id,
        tenant_id=tenant_id,
        normalized_email="canonical.persistence@example.com",
        identity_type=IdentityType.PERSON,
        legal_name=LegalName(
            given_names=("Canonical",),
            middle_names=("Persistence",),
            family_name="Person",
        ),
        preferred_name="Canonical",
        alternative_names=(
            IdentityName(
                name_type=NameType.PREFERRED,
                display_name="Canonical",
                effective_from=now,
            ),
        ),
        contact_points=(
            ContactPoint(
                contact_type=ContactPointType.EMAIL,
                value="canonical.persistence@example.com",
                verified=True,
                primary=True,
            ),
        ),
        addresses=(
            IdentityAddress(
                address_type=AddressType.RESIDENTIAL,
                line1="1 Identity Street",
                locality="Melbourne",
                region="VIC",
                postal_code="3000",
                country_code="AU",
            ),
        ),
        identifiers=(
            IdentityIdentifier(
                identifier_type=IdentifierType.NOVAID,
                value="nid-canonical-persistence",
                issuer="NovaID",
                primary=True,
            ),
        ),
        verification_status=VerificationStatus.VERIFIED,
        assurance_level=AssuranceLevel.NID_AL2,
        metadata={
            "source": "repository-round-trip",
            "schema_version": 1,
        },
    )

    store = NovaIDUnitOfWork()

    with store:
        store.connection.execute(
            "INSERT INTO novaid_tenants("
            "tenant_id,name,status,created_at,updated_at,version"
            ") VALUES(?,?,?,?,?,1)",
            (
                tenant_id,
                "Canonical Persistence Tenant",
                "ACTIVE",
                    now.isoformat(),
                    now.isoformat(),
            ),
        )

        store.add_identity(identity)

        context = RequestContext(
            tenant_id=tenant_id,
            actor_identity_id=uid(),
            actor_membership_id=uid(),
            correlation_id=uid(),
            request_id=uid(),
            authentication_strength="PASSWORD_OTP",
        )

        restored = store.get_identity(
            context,
            identity_id,
        )

    assert restored is not None
    assert restored.identity_id == identity.identity_id
    assert restored.identity_type is IdentityType.PERSON
    assert restored.legal_name == identity.legal_name
    assert restored.preferred_name == identity.preferred_name
    assert restored.alternative_names == identity.alternative_names
    assert restored.contact_points == identity.contact_points
    assert restored.addresses == identity.addresses
    assert restored.identifiers == identity.identifiers
    assert restored.verification_status is VerificationStatus.VERIFIED
    assert restored.assurance_level is AssuranceLevel.NID_AL2
    assert restored.metadata == identity.metadata


def test_sqlite_identity_read_is_tenant_isolated() -> None:
    tenant_a = uid()
    tenant_b = uid()
    identity_id = uid()
    now = datetime.now(UTC)

    store = NovaIDUnitOfWork()

    with store:
        for tenant_id, name in (
            (tenant_a, "Tenant A"),
            (tenant_b, "Tenant B"),
        ):
            store.connection.execute(
                "INSERT INTO novaid_tenants("
                "tenant_id,name,status,created_at,updated_at,version"
                ") VALUES(?,?,?,?,?,1)",
                (
                    tenant_id,
                    name,
                    "ACTIVE",
                    now.isoformat(),
                    now.isoformat(),
                ),
            )

        store.add_identity(
            Identity(
                identity_id=identity_id,
                tenant_id=tenant_a,
                normalized_email="tenant-a@example.com",
            )
        )

        tenant_a_context = RequestContext(
            tenant_id=tenant_a,
            actor_identity_id=uid(),
            actor_membership_id=uid(),
            correlation_id=uid(),
            request_id=uid(),
            authentication_strength="PASSWORD_OTP",
        )

        tenant_b_context = RequestContext(
            tenant_id=tenant_b,
            actor_identity_id=uid(),
            actor_membership_id=uid(),
            correlation_id=uid(),
            request_id=uid(),
            authentication_strength="PASSWORD_OTP",
        )

        assert store.get_identity(
            tenant_a_context,
            identity_id,
        ) is not None

        with pytest.raises(
            LookupError,
            match="TENANT_ACCESS_DENIED",
        ):
            store.get_identity(
                tenant_b_context,
                identity_id,
            )
