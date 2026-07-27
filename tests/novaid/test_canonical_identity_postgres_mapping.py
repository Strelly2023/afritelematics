from datetime import UTC, datetime
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    AssuranceLevel,
    Identity,
    IdentityType,
    LegalName,
    RequestContext,
    VerificationStatus,
)
from afritech.novaid.persistence.postgres import (
    PostgresNovaIdUnitOfWork,
)


def uid() -> str:
    return str(uuid4())


class FakeResult:
    def __init__(self, row=None) -> None:
        self._row = row
        self.rowcount = 1 if row is not None else 0

    def fetchone(self):
        return self._row

    def fetchall(self):
        return []


class FakeConnection:
    def __init__(self, row=None) -> None:
        self.row = row
        self.calls: list[tuple[str, tuple]] = []

    def execute(self, sql: str, parameters: tuple = ()) -> FakeResult:
        self.calls.append((sql, parameters))
        return FakeResult(self.row)


def build_uow(connection: FakeConnection) -> PostgresNovaIdUnitOfWork:
    store = object.__new__(PostgresNovaIdUnitOfWork)
    store._connection = connection
    store.connection = connection
    return store


def test_postgres_add_identity_writes_canonical_profile() -> None:
    connection = FakeConnection()
    store = build_uow(connection)

    identity = Identity(
        identity_id=uid(),
        tenant_id=uid(),
        normalized_email="postgres.mapping@example.com",
        legal_name=LegalName(
            given_names=("Postgres",),
            family_name="Mapping",
        ),
        verification_status=VerificationStatus.VERIFIED,
        assurance_level=AssuranceLevel.NID_AL2,
        metadata={"source": "postgres-mapping-test"},
    )

    store.add_identity(identity)

    assert len(connection.calls) == 1

    sql, parameters = connection.calls[0]

    assert "identity_type" in sql
    assert "legal_name" in sql
    assert "verification_status" in sql
    assert "assurance_level" in sql
    assert "metadata" in sql

    assert len(parameters) == 17
    assert parameters[7] == IdentityType.PERSON.value
    assert parameters[14] == VerificationStatus.VERIFIED.value
    assert parameters[15] == AssuranceLevel.NID_AL2.value
    assert '"source":"postgres-mapping-test"' in parameters[16]


def test_postgres_get_identity_decodes_canonical_profile() -> None:
    now = datetime.now(UTC)
    tenant_id = uid()
    identity_id = uid()

    row = {
        "identity_id": identity_id,
        "tenant_id": tenant_id,
        "normalized_email": "postgres.read@example.com",
        "status": "PENDING_VERIFICATION",
        "created_at": now,
        "updated_at": now,
        "version": 1,
        "identity_type": "PERSON",
        "legal_name": {
            "given_names": ["Postgres"],
            "middle_names": [],
            "family_name": "Read",
            "honorific": None,
            "suffix": None,
        },
        "preferred_name": "Postgres",
        "alternative_names": [],
        "contact_points": [],
        "addresses": [],
        "identifiers": [],
        "verification_status": "VERIFIED",
        "assurance_level": "NID-AL2",
        "metadata": {"source": "postgres-read-test"},
    }

    connection = FakeConnection(row)
    store = build_uow(connection)

    context = RequestContext(
        tenant_id=tenant_id,
        actor_identity_id=uid(),
        actor_membership_id=uid(),
        correlation_id=uid(),
        request_id=uid(),
        authentication_strength="PASSWORD_OTP",
    )

    restored = store.get_identity(context, identity_id)

    assert restored.legal_name is not None
    assert restored.legal_name.family_name == "Read"
    assert restored.verification_status is VerificationStatus.VERIFIED
    assert restored.assurance_level is AssuranceLevel.NID_AL2
    assert restored.metadata == {"source": "postgres-read-test"}

    sql, parameters = connection.calls[0]
    assert "tenant_id=?" in sql
    assert parameters == (identity_id, tenant_id)


def test_postgres_get_identity_fails_closed_for_missing_tenant_row() -> None:
    connection = FakeConnection(None)
    store = build_uow(connection)

    context = RequestContext(
        tenant_id=uid(),
        actor_identity_id=uid(),
        actor_membership_id=uid(),
        correlation_id=uid(),
        request_id=uid(),
        authentication_strength="PASSWORD_OTP",
    )

    with pytest.raises(LookupError, match="TENANT_ACCESS_DENIED"):
        store.get_identity(context, uid())
