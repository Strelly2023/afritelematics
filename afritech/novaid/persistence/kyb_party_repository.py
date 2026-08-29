"""Dedicated persistence for NovaID KYB party authorities.

NR-PROD-002E-D5.

The repository keeps BeneficialOwner and BusinessRepresentative records
separate from the generic identity/KYB payload so that tenant, legal
entity, lifecycle and verification state remain queryable and governed.

SQLite and PostgreSQL expose equivalent repository semantics.
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol

from afritech.novaid.domain.beneficial_ownership import (
    BeneficialOwner,
    BeneficialOwnerControlBasis,
    BeneficialOwnerVerificationStatus,
)
from afritech.novaid.domain.business_representative import (
    BusinessRepresentative,
    BusinessRepresentativeRole,
    BusinessRepresentativeVerificationStatus,
)


class KYBPartyPersistenceError(RuntimeError):
    """Base persistence error."""


class KYBPartyNotFoundError(KYBPartyPersistenceError):
    """Requested party is absent inside the requested tenant."""


class KYBPartyTenantMismatchError(KYBPartyPersistenceError):
    """A stored row does not belong to the requested tenant."""


class KYBPartyRepository(Protocol):
    def save_beneficial_owner(
        self,
        owner: BeneficialOwner,
    ) -> None: ...

    def get_beneficial_owner(
        self,
        *,
        tenant_id: str,
        beneficial_owner_id: str,
    ) -> BeneficialOwner | None: ...

    def list_beneficial_owners(
        self,
        *,
        tenant_id: str,
        legal_entity_id: str,
    ) -> tuple[BeneficialOwner, ...]: ...

    def delete_beneficial_owner(
        self,
        *,
        tenant_id: str,
        beneficial_owner_id: str,
    ) -> bool: ...

    def save_business_representative(
        self,
        representative: BusinessRepresentative,
    ) -> None: ...

    def get_business_representative(
        self,
        *,
        tenant_id: str,
        representative_id: str,
    ) -> BusinessRepresentative | None: ...

    def list_business_representatives(
        self,
        *,
        tenant_id: str,
        legal_entity_id: str,
    ) -> tuple[BusinessRepresentative, ...]: ...

    def delete_business_representative(
        self,
        *,
        tenant_id: str,
        representative_id: str,
    ) -> bool: ...


def _json_tuple(values: tuple[Any, ...]) -> str:
    return json.dumps(
        [
            (
                value.value
                if hasattr(value, "value")
                else value
            )
            for value in values
        ],
        separators=(",", ":"),
    )


def _json_load_tuple(
    value: str,
) -> tuple[str, ...]:
    payload = json.loads(value)

    if not isinstance(payload, list):
        raise KYBPartyPersistenceError(
            "KYB_PARTY_INVALID_JSON_ARRAY"
        )

    return tuple(
        str(item)
        for item in payload
    )


def _decimal_text(
    value: Decimal | None,
) -> str | None:
    if value is None:
        return None

    return str(value)


def _owner_from_row(
    row: tuple[Any, ...],
) -> BeneficialOwner:
    return BeneficialOwner(
        beneficial_owner_id=str(row[0]),
        tenant_id=str(row[1]),
        legal_entity_id=str(row[2]),
        identity_id=str(row[3]),
        control_bases=tuple(
            BeneficialOwnerControlBasis(item)
            for item in _json_load_tuple(
                str(row[4])
            )
        ),
        ownership_percentage=(
            None
            if row[5] is None
            else Decimal(str(row[5]))
        ),
        verification_status=(
            BeneficialOwnerVerificationStatus(
                str(row[6])
            )
        ),
        effective_from=datetime.fromisoformat(
            str(row[7])
        ),
        effective_to=(
            None
            if row[8] is None
            else datetime.fromisoformat(
                str(row[8])
            )
        ),
        provider_reference=(
            None
            if row[9] is None
            else str(row[9])
        ),
        evidence_refs=_json_load_tuple(
            str(row[10])
        ),
    )


def _representative_from_row(
    row: tuple[Any, ...],
) -> BusinessRepresentative:
    return BusinessRepresentative(
        representative_id=str(row[0]),
        tenant_id=str(row[1]),
        legal_entity_id=str(row[2]),
        identity_id=str(row[3]),
        roles=tuple(
            BusinessRepresentativeRole(item)
            for item in _json_load_tuple(
                str(row[4])
            )
        ),
        verification_status=(
            BusinessRepresentativeVerificationStatus(
                str(row[5])
            )
        ),
        effective_from=datetime.fromisoformat(
            str(row[6])
        ),
        effective_to=(
            None
            if row[7] is None
            else datetime.fromisoformat(
                str(row[7])
            )
        ),
        authority_reference=(
            None
            if row[8] is None
            else str(row[8])
        ),
        provider_reference=(
            None
            if row[9] is None
            else str(row[9])
        ),
        evidence_refs=_json_load_tuple(
            str(row[10])
        ),
    )


SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS novaid_beneficial_owners (
    beneficial_owner_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    legal_entity_id TEXT NOT NULL,
    identity_id TEXT NOT NULL,
    control_bases_json TEXT NOT NULL,
    ownership_percentage TEXT NULL,
    verification_status TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT NULL,
    provider_reference TEXT NULL,
    evidence_refs_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, beneficial_owner_id)
);

CREATE INDEX IF NOT EXISTS
    idx_novaid_beneficial_owners_tenant_entity
ON novaid_beneficial_owners (
    tenant_id,
    legal_entity_id
);

CREATE TABLE IF NOT EXISTS novaid_business_representatives (
    representative_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    legal_entity_id TEXT NOT NULL,
    identity_id TEXT NOT NULL,
    roles_json TEXT NOT NULL,
    verification_status TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT NULL,
    authority_reference TEXT NULL,
    provider_reference TEXT NULL,
    evidence_refs_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, representative_id)
);

CREATE INDEX IF NOT EXISTS
    idx_novaid_business_representatives_tenant_entity
ON novaid_business_representatives (
    tenant_id,
    legal_entity_id
);
"""


POSTGRES_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS novaid_beneficial_owners (
        beneficial_owner_id TEXT NOT NULL,
        tenant_id TEXT NOT NULL,
        legal_entity_id TEXT NOT NULL,
        identity_id TEXT NOT NULL,
        control_bases_json TEXT NOT NULL,
        ownership_percentage TEXT NULL,
        verification_status TEXT NOT NULL,
        effective_from TEXT NOT NULL,
        effective_to TEXT NULL,
        provider_reference TEXT NULL,
        evidence_refs_json TEXT NOT NULL,
        PRIMARY KEY (tenant_id, beneficial_owner_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS
        idx_novaid_beneficial_owners_tenant_entity
    ON novaid_beneficial_owners (
        tenant_id,
        legal_entity_id
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS novaid_business_representatives (
        representative_id TEXT NOT NULL,
        tenant_id TEXT NOT NULL,
        legal_entity_id TEXT NOT NULL,
        identity_id TEXT NOT NULL,
        roles_json TEXT NOT NULL,
        verification_status TEXT NOT NULL,
        effective_from TEXT NOT NULL,
        effective_to TEXT NULL,
        authority_reference TEXT NULL,
        provider_reference TEXT NULL,
        evidence_refs_json TEXT NOT NULL,
        PRIMARY KEY (tenant_id, representative_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS
        idx_novaid_business_representatives_tenant_entity
    ON novaid_business_representatives (
        tenant_id,
        legal_entity_id
    )
    """,
)


class SQLiteKYBPartyRepository:
    """SQLite implementation using an injected sqlite3 connection."""

    def __init__(
        self,
        connection: Any,
    ) -> None:
        self._connection = connection

    def ensure_schema(self) -> None:
        self._connection.executescript(
            SQLITE_SCHEMA
        )
        self._connection.commit()

    def save_beneficial_owner(
        self,
        owner: BeneficialOwner,
    ) -> None:
        self._connection.execute(
            """
            INSERT INTO novaid_beneficial_owners (
                beneficial_owner_id,
                tenant_id,
                legal_entity_id,
                identity_id,
                control_bases_json,
                ownership_percentage,
                verification_status,
                effective_from,
                effective_to,
                provider_reference,
                evidence_refs_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (
                tenant_id,
                beneficial_owner_id
            )
            DO UPDATE SET
                legal_entity_id = excluded.legal_entity_id,
                identity_id = excluded.identity_id,
                control_bases_json = excluded.control_bases_json,
                ownership_percentage = excluded.ownership_percentage,
                verification_status = excluded.verification_status,
                effective_from = excluded.effective_from,
                effective_to = excluded.effective_to,
                provider_reference = excluded.provider_reference,
                evidence_refs_json = excluded.evidence_refs_json
            """,
            (
                owner.beneficial_owner_id,
                owner.tenant_id,
                owner.legal_entity_id,
                owner.identity_id,
                _json_tuple(
                    owner.control_bases
                ),
                _decimal_text(
                    owner.ownership_percentage
                ),
                owner.verification_status.value,
                owner.effective_from.isoformat(),
                (
                    None
                    if owner.effective_to is None
                    else owner.effective_to.isoformat()
                ),
                owner.provider_reference,
                _json_tuple(
                    owner.evidence_refs
                ),
            ),
        )
        self._connection.commit()

    def get_beneficial_owner(
        self,
        *,
        tenant_id: str,
        beneficial_owner_id: str,
    ) -> BeneficialOwner | None:
        row = self._connection.execute(
            """
            SELECT
                beneficial_owner_id,
                tenant_id,
                legal_entity_id,
                identity_id,
                control_bases_json,
                ownership_percentage,
                verification_status,
                effective_from,
                effective_to,
                provider_reference,
                evidence_refs_json
            FROM novaid_beneficial_owners
            WHERE tenant_id = ?
              AND beneficial_owner_id = ?
            """,
            (
                tenant_id,
                beneficial_owner_id,
            ),
        ).fetchone()

        if row is None:
            return None

        return _owner_from_row(
            tuple(row)
        )

    def list_beneficial_owners(
        self,
        *,
        tenant_id: str,
        legal_entity_id: str,
    ) -> tuple[BeneficialOwner, ...]:
        rows = self._connection.execute(
            """
            SELECT
                beneficial_owner_id,
                tenant_id,
                legal_entity_id,
                identity_id,
                control_bases_json,
                ownership_percentage,
                verification_status,
                effective_from,
                effective_to,
                provider_reference,
                evidence_refs_json
            FROM novaid_beneficial_owners
            WHERE tenant_id = ?
              AND legal_entity_id = ?
            ORDER BY beneficial_owner_id
            """,
            (
                tenant_id,
                legal_entity_id,
            ),
        ).fetchall()

        return tuple(
            _owner_from_row(
                tuple(row)
            )
            for row in rows
        )

    def delete_beneficial_owner(
        self,
        *,
        tenant_id: str,
        beneficial_owner_id: str,
    ) -> bool:
        cursor = self._connection.execute(
            """
            DELETE FROM novaid_beneficial_owners
            WHERE tenant_id = ?
              AND beneficial_owner_id = ?
            """,
            (
                tenant_id,
                beneficial_owner_id,
            ),
        )

        self._connection.commit()

        return cursor.rowcount == 1

    def save_business_representative(
        self,
        representative: BusinessRepresentative,
    ) -> None:
        self._connection.execute(
            """
            INSERT INTO novaid_business_representatives (
                representative_id,
                tenant_id,
                legal_entity_id,
                identity_id,
                roles_json,
                verification_status,
                effective_from,
                effective_to,
                authority_reference,
                provider_reference,
                evidence_refs_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (
                tenant_id,
                representative_id
            )
            DO UPDATE SET
                legal_entity_id = excluded.legal_entity_id,
                identity_id = excluded.identity_id,
                roles_json = excluded.roles_json,
                verification_status = excluded.verification_status,
                effective_from = excluded.effective_from,
                effective_to = excluded.effective_to,
                authority_reference = excluded.authority_reference,
                provider_reference = excluded.provider_reference,
                evidence_refs_json = excluded.evidence_refs_json
            """,
            (
                representative.representative_id,
                representative.tenant_id,
                representative.legal_entity_id,
                representative.identity_id,
                _json_tuple(
                    representative.roles
                ),
                representative.verification_status.value,
                representative.effective_from.isoformat(),
                (
                    None
                    if representative.effective_to is None
                    else representative.effective_to.isoformat()
                ),
                representative.authority_reference,
                representative.provider_reference,
                _json_tuple(
                    representative.evidence_refs
                ),
            ),
        )

        self._connection.commit()

    def get_business_representative(
        self,
        *,
        tenant_id: str,
        representative_id: str,
    ) -> BusinessRepresentative | None:
        row = self._connection.execute(
            """
            SELECT
                representative_id,
                tenant_id,
                legal_entity_id,
                identity_id,
                roles_json,
                verification_status,
                effective_from,
                effective_to,
                authority_reference,
                provider_reference,
                evidence_refs_json
            FROM novaid_business_representatives
            WHERE tenant_id = ?
              AND representative_id = ?
            """,
            (
                tenant_id,
                representative_id,
            ),
        ).fetchone()

        if row is None:
            return None

        return _representative_from_row(
            tuple(row)
        )

    def list_business_representatives(
        self,
        *,
        tenant_id: str,
        legal_entity_id: str,
    ) -> tuple[BusinessRepresentative, ...]:
        rows = self._connection.execute(
            """
            SELECT
                representative_id,
                tenant_id,
                legal_entity_id,
                identity_id,
                roles_json,
                verification_status,
                effective_from,
                effective_to,
                authority_reference,
                provider_reference,
                evidence_refs_json
            FROM novaid_business_representatives
            WHERE tenant_id = ?
              AND legal_entity_id = ?
            ORDER BY representative_id
            """,
            (
                tenant_id,
                legal_entity_id,
            ),
        ).fetchall()

        return tuple(
            _representative_from_row(
                tuple(row)
            )
            for row in rows
        )

    def delete_business_representative(
        self,
        *,
        tenant_id: str,
        representative_id: str,
    ) -> bool:
        cursor = self._connection.execute(
            """
            DELETE FROM novaid_business_representatives
            WHERE tenant_id = ?
              AND representative_id = ?
            """,
            (
                tenant_id,
                representative_id,
            ),
        )

        self._connection.commit()

        return cursor.rowcount == 1


class PostgresKYBPartyRepository:
    """PostgreSQL implementation using an injected psycopg connection."""

    def __init__(
        self,
        connection: Any,
    ) -> None:
        self._connection = connection

    def ensure_schema(self) -> None:
        with self._connection.cursor() as cursor:
            for statement in POSTGRES_SCHEMA_STATEMENTS:
                cursor.execute(
                    statement
                )

        self._connection.commit()

    def save_beneficial_owner(
        self,
        owner: BeneficialOwner,
    ) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO novaid_beneficial_owners (
                    beneficial_owner_id,
                    tenant_id,
                    legal_entity_id,
                    identity_id,
                    control_bases_json,
                    ownership_percentage,
                    verification_status,
                    effective_from,
                    effective_to,
                    provider_reference,
                    evidence_refs_json
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (
                    tenant_id,
                    beneficial_owner_id
                )
                DO UPDATE SET
                    legal_entity_id = EXCLUDED.legal_entity_id,
                    identity_id = EXCLUDED.identity_id,
                    control_bases_json = EXCLUDED.control_bases_json,
                    ownership_percentage = EXCLUDED.ownership_percentage,
                    verification_status = EXCLUDED.verification_status,
                    effective_from = EXCLUDED.effective_from,
                    effective_to = EXCLUDED.effective_to,
                    provider_reference = EXCLUDED.provider_reference,
                    evidence_refs_json = EXCLUDED.evidence_refs_json
                """,
                (
                    owner.beneficial_owner_id,
                    owner.tenant_id,
                    owner.legal_entity_id,
                    owner.identity_id,
                    _json_tuple(
                        owner.control_bases
                    ),
                    _decimal_text(
                        owner.ownership_percentage
                    ),
                    owner.verification_status.value,
                    owner.effective_from.isoformat(),
                    (
                        None
                        if owner.effective_to is None
                        else owner.effective_to.isoformat()
                    ),
                    owner.provider_reference,
                    _json_tuple(
                        owner.evidence_refs
                    ),
                ),
            )

        self._connection.commit()

    def get_beneficial_owner(
        self,
        *,
        tenant_id: str,
        beneficial_owner_id: str,
    ) -> BeneficialOwner | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    beneficial_owner_id,
                    tenant_id,
                    legal_entity_id,
                    identity_id,
                    control_bases_json,
                    ownership_percentage,
                    verification_status,
                    effective_from,
                    effective_to,
                    provider_reference,
                    evidence_refs_json
                FROM novaid_beneficial_owners
                WHERE tenant_id = %s
                  AND beneficial_owner_id = %s
                """,
                (
                    tenant_id,
                    beneficial_owner_id,
                ),
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return _owner_from_row(
            tuple(row)
        )

    def list_beneficial_owners(
        self,
        *,
        tenant_id: str,
        legal_entity_id: str,
    ) -> tuple[BeneficialOwner, ...]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    beneficial_owner_id,
                    tenant_id,
                    legal_entity_id,
                    identity_id,
                    control_bases_json,
                    ownership_percentage,
                    verification_status,
                    effective_from,
                    effective_to,
                    provider_reference,
                    evidence_refs_json
                FROM novaid_beneficial_owners
                WHERE tenant_id = %s
                  AND legal_entity_id = %s
                ORDER BY beneficial_owner_id
                """,
                (
                    tenant_id,
                    legal_entity_id,
                ),
            )

            rows = cursor.fetchall()

        return tuple(
            _owner_from_row(
                tuple(row)
            )
            for row in rows
        )

    def delete_beneficial_owner(
        self,
        *,
        tenant_id: str,
        beneficial_owner_id: str,
    ) -> bool:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM novaid_beneficial_owners
                WHERE tenant_id = %s
                  AND beneficial_owner_id = %s
                """,
                (
                    tenant_id,
                    beneficial_owner_id,
                ),
            )

            deleted = cursor.rowcount

        self._connection.commit()

        return deleted == 1

    def save_business_representative(
        self,
        representative: BusinessRepresentative,
    ) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO novaid_business_representatives (
                    representative_id,
                    tenant_id,
                    legal_entity_id,
                    identity_id,
                    roles_json,
                    verification_status,
                    effective_from,
                    effective_to,
                    authority_reference,
                    provider_reference,
                    evidence_refs_json
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (
                    tenant_id,
                    representative_id
                )
                DO UPDATE SET
                    legal_entity_id = EXCLUDED.legal_entity_id,
                    identity_id = EXCLUDED.identity_id,
                    roles_json = EXCLUDED.roles_json,
                    verification_status = EXCLUDED.verification_status,
                    effective_from = EXCLUDED.effective_from,
                    effective_to = EXCLUDED.effective_to,
                    authority_reference = EXCLUDED.authority_reference,
                    provider_reference = EXCLUDED.provider_reference,
                    evidence_refs_json = EXCLUDED.evidence_refs_json
                """,
                (
                    representative.representative_id,
                    representative.tenant_id,
                    representative.legal_entity_id,
                    representative.identity_id,
                    _json_tuple(
                        representative.roles
                    ),
                    representative.verification_status.value,
                    representative.effective_from.isoformat(),
                    (
                        None
                        if representative.effective_to is None
                        else representative.effective_to.isoformat()
                    ),
                    representative.authority_reference,
                    representative.provider_reference,
                    _json_tuple(
                        representative.evidence_refs
                    ),
                ),
            )

        self._connection.commit()

    def get_business_representative(
        self,
        *,
        tenant_id: str,
        representative_id: str,
    ) -> BusinessRepresentative | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    representative_id,
                    tenant_id,
                    legal_entity_id,
                    identity_id,
                    roles_json,
                    verification_status,
                    effective_from,
                    effective_to,
                    authority_reference,
                    provider_reference,
                    evidence_refs_json
                FROM novaid_business_representatives
                WHERE tenant_id = %s
                  AND representative_id = %s
                """,
                (
                    tenant_id,
                    representative_id,
                ),
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return _representative_from_row(
            tuple(row)
        )

    def list_business_representatives(
        self,
        *,
        tenant_id: str,
        legal_entity_id: str,
    ) -> tuple[BusinessRepresentative, ...]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    representative_id,
                    tenant_id,
                    legal_entity_id,
                    identity_id,
                    roles_json,
                    verification_status,
                    effective_from,
                    effective_to,
                    authority_reference,
                    provider_reference,
                    evidence_refs_json
                FROM novaid_business_representatives
                WHERE tenant_id = %s
                  AND legal_entity_id = %s
                ORDER BY representative_id
                """,
                (
                    tenant_id,
                    legal_entity_id,
                ),
            )

            rows = cursor.fetchall()

        return tuple(
            _representative_from_row(
                tuple(row)
            )
            for row in rows
        )

    def delete_business_representative(
        self,
        *,
        tenant_id: str,
        representative_id: str,
    ) -> bool:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM novaid_business_representatives
                WHERE tenant_id = %s
                  AND representative_id = %s
                """,
                (
                    tenant_id,
                    representative_id,
                ),
            )

            deleted = cursor.rowcount

        self._connection.commit()

        return deleted == 1


__all__ = [
    "KYBPartyPersistenceError",
    "KYBPartyNotFoundError",
    "KYBPartyTenantMismatchError",
    "KYBPartyRepository",
    "SQLiteKYBPartyRepository",
    "PostgresKYBPartyRepository",
    "SQLITE_SCHEMA",
    "POSTGRES_SCHEMA_STATEMENTS",
]
