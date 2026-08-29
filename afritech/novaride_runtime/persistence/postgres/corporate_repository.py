"""PostgreSQL persistence for NovaRide Corporate Mobility aggregates.

NovaRide owns CorporateAccount and CorporateBooking mobility workflow state.

NovaPay remains authoritative for wallets, ledger, payment execution,
settlement, reconciliation, and financial movement.

NovaID remains authoritative for identity and authentication.

The corporate_travel_policies table is intentionally not exposed through a
synthetic repository because RuntimeRepositories currently defines no
corresponding CorporateTravelPolicy aggregate repository.
"""

from __future__ import annotations

from typing import Any, Mapping

from afritech.novaride_runtime.models import (
    CorporateAccount,
    CorporateBooking,
)
from afritech.novaride_runtime.persistence.postgres.base_repository import (
    PostgresAggregateRepository,
    SyncPostgresConnection,
)
from afritech.novaride_runtime.persistence.postgres.unit_of_work import (
    PostgresUnitOfWork,
    PostgresUnitOfWorkConfig,
)


def _encode_corporate_account(
    account: CorporateAccount,
) -> Mapping[str, Any]:
    return {
        "account_id": account.id,
        "tenant_id": account.tenant_id,
        "organization_id": account.organization_id,
        "region_code": account.region_code,
        "name": account.name,
        "wallet_reference": account.wallet_reference,
        "aggregate_version": account.aggregate_version,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
    }


def _decode_corporate_account(
    row: Mapping[str, Any],
) -> CorporateAccount:
    return CorporateAccount(
        id=str(row["account_id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(
            row["organization_id"]
        ),
        region_code=str(
            row["region_code"]
        ),
        aggregate_version=int(
            row["aggregate_version"]
        ),
        schema_version="2026.2",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        name=str(row["name"]),
        wallet_reference=(
            None
            if row.get("wallet_reference") is None
            else str(row["wallet_reference"])
        ),
    )


def _encode_corporate_booking(
    booking: CorporateBooking,
) -> Mapping[str, Any]:
    return {
        "corporate_booking_id": booking.id,
        "tenant_id": booking.tenant_id,
        "organization_id": booking.organization_id,
        "region_code": booking.region_code,
        "account_id": booking.account_id,
        "employee_id": booking.employee_id,
        "booking_id": booking.booking_id,
        "cost_center_id": booking.cost_center_id,
        "aggregate_version": booking.aggregate_version,
        "created_at": booking.created_at,
        "updated_at": booking.updated_at,
    }


def _decode_corporate_booking(
    row: Mapping[str, Any],
) -> CorporateBooking:
    return CorporateBooking(
        id=str(row["corporate_booking_id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(
            row["organization_id"]
        ),
        region_code=str(
            row["region_code"]
        ),
        aggregate_version=int(
            row["aggregate_version"]
        ),
        schema_version="2026.2",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        account_id=str(
            row["account_id"]
        ),
        employee_id=str(
            row["employee_id"]
        ),
        booking_id=str(
            row["booking_id"]
        ),
        cost_center_id=(
            None
            if row.get("cost_center_id") is None
            else str(row["cost_center_id"])
        ),
    )


class PostgresCorporateAccountRepository(
    PostgresAggregateRepository[CorporateAccount]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="corporate_accounts",
            id_column="account_id",
            to_record=_encode_corporate_account,
            from_record=_decode_corporate_account,
        )


class PostgresCorporateBookingRepository(
    PostgresAggregateRepository[CorporateBooking]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="corporate_bookings",
            id_column="corporate_booking_id",
            to_record=_encode_corporate_booking,
            from_record=_decode_corporate_booking,
        )


__all__ = [
    "PostgresCorporateAccountRepository",
    "PostgresCorporateBookingRepository",
    "PostgresUnitOfWork",
    "PostgresUnitOfWorkConfig",
]
