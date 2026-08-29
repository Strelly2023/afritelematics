"""PostgreSQL RuntimeRepositories composition for NovaRide.

This module constructs all synchronous runtime repository adapters
against one provided PostgreSQL connection.

It deliberately does not:
- open or close connections;
- commit or roll back transactions;
- set tenant context;
- activate PostgreSQL in create_runtime();
- alter settings-driven persistence selection.

Those responsibilities remain with PostgresUnitOfWork and later
composition/activation gates.
"""

from __future__ import annotations

from dataclasses import dataclass

from afritech.novaride_runtime.persistence.memory import (
    RuntimeRepositories,
)
from afritech.novaride_runtime.persistence.postgres.booking_repository import (
    PostgresBookingRepository,
    PostgresFareQuoteRepository,
)
from afritech.novaride_runtime.persistence.postgres.connection import (
    PostgresConnectionProtocol,
)
from afritech.novaride_runtime.persistence.postgres.corporate_repository import (
    PostgresCorporateAccountRepository,
    PostgresCorporateBookingRepository,
)
from afritech.novaride_runtime.persistence.postgres.driver_repository import (
    PostgresDriverAvailabilityRepository,
    PostgresDriverEligibilityRepository,
    PostgresDriverProfileRepository,
    PostgresDriverShiftRepository,
)
from afritech.novaride_runtime.persistence.postgres.event_outbox_repository import (
    PostgresEventOutboxRepository,
)
from afritech.novaride_runtime.persistence.postgres.operations_workspace_repository import (
    PostgresOperationsWorkspaceRepository,
)
from afritech.novaride_runtime.persistence.postgres.event_repository import (
    PostgresEventRepository,
)
from afritech.novaride_runtime.persistence.postgres.fleet_repository import (
    PostgresFleetComplianceRepository,
    PostgresFleetRepository,
    PostgresFleetVehicleRepository,
)
from afritech.novaride_runtime.persistence.postgres.idempotency_repository import (
    PostgresIdempotencyRepository,
)
from afritech.novaride_runtime.persistence.postgres.logistics_repository import (
    PostgresDeliveryRepository,
)
from afritech.novaride_runtime.persistence.postgres.operator_repository import (
    PostgresOperatorCommandRepository,
)
from afritech.novaride_runtime.persistence.postgres.projection_repository import (
    PostgresProjectionStateRepository,
    PostgresProjectionVersionRepository,
)
from afritech.novaride_runtime.persistence.postgres.resilience_runtime_repository import (
    PostgresRuntimeConflictRecordRepository,
    PostgresRuntimeFailoverEventRepository,
    PostgresRuntimeOfflineOperationRepository,
    PostgresRuntimeProviderHealthRepository,
    PostgresRuntimeProviderRouteRepository,
    PostgresRuntimeResilienceEvidenceRepository,
    PostgresRuntimeSyncSessionRepository,
)
from afritech.novaride_runtime.persistence.postgres.rider_repository import (
    PostgresRiderRepository,
)
from afritech.novaride_runtime.persistence.postgres.rating_repository import PostgresRatingRepository
from afritech.novaride_runtime.persistence.postgres.support_repository import PostgresSupportCaseRepository
from afritech.novaride_runtime.persistence.postgres.safety_repository import (
    PostgresEmergencyRepository,
    PostgresIncidentRepository,
)
from afritech.novaride_runtime.persistence.postgres.transit_repository import (
    PostgresTransitJourneyRepository,
)
from afritech.novaride_runtime.persistence.postgres.trip_repository import (
    PostgresDriverOfferRepository,
    PostgresTripRepository,
)


@dataclass(frozen=True, slots=True)
class PostgresRuntimeSupportRepositories:
    """Support components outside the 28 RuntimeRepositories fields."""

    event_outbox: PostgresEventOutboxRepository
    projection_state: PostgresProjectionStateRepository
    projection_versions: PostgresProjectionVersionRepository
    operations_workspace: PostgresOperationsWorkspaceRepository


@dataclass(frozen=True, slots=True)
class PostgresRuntimeRepositoryBundle:
    """Transaction-scoped NovaRide PostgreSQL repository bundle."""

    repositories: RuntimeRepositories
    support: PostgresRuntimeSupportRepositories
    connection: PostgresConnectionProtocol


def create_postgres_runtime_repository_bundle(
    connection: PostgresConnectionProtocol,
) -> PostgresRuntimeRepositoryBundle:
    """Create all PostgreSQL runtime repositories on one connection."""

    repositories = RuntimeRepositories(
        ratings=PostgresRatingRepository(connection),
        riders=PostgresRiderRepository(connection),
        drivers=PostgresDriverProfileRepository(connection),
        eligibility=PostgresDriverEligibilityRepository(connection),
        availability=PostgresDriverAvailabilityRepository(connection),
        shifts=PostgresDriverShiftRepository(connection),
        offers=PostgresDriverOfferRepository(connection),
        bookings=PostgresBookingRepository(connection),
        fare_quotes=PostgresFareQuoteRepository(connection),
        trips=PostgresTripRepository(connection),
        support_cases=PostgresSupportCaseRepository(connection),
        emergencies=PostgresEmergencyRepository(connection),
        incidents=PostgresIncidentRepository(connection),
        fleets=PostgresFleetRepository(connection),
        fleet_vehicles=PostgresFleetVehicleRepository(connection),
        fleet_compliance=PostgresFleetComplianceRepository(connection),
        deliveries=PostgresDeliveryRepository(connection),
        corporate_accounts=PostgresCorporateAccountRepository(connection),
        corporate_bookings=PostgresCorporateBookingRepository(connection),
        transit_journeys=PostgresTransitJourneyRepository(connection),
        operator_commands=PostgresOperatorCommandRepository(connection),
        offline_operations=PostgresRuntimeOfflineOperationRepository(
            connection
        ),
        resilience_evidence=PostgresRuntimeResilienceEvidenceRepository(
            connection
        ),
        provider_health=PostgresRuntimeProviderHealthRepository(
            connection
        ),
        provider_routes=PostgresRuntimeProviderRouteRepository(
            connection
        ),
        sync_sessions=PostgresRuntimeSyncSessionRepository(
            connection
        ),
        conflict_records=PostgresRuntimeConflictRecordRepository(
            connection
        ),
        failover_events=PostgresRuntimeFailoverEventRepository(
            connection
        ),
        events=PostgresEventRepository(connection),
        idempotency=PostgresIdempotencyRepository(connection),
    )

    support = PostgresRuntimeSupportRepositories(
        event_outbox=PostgresEventOutboxRepository(
            connection
        ),
        projection_state=PostgresProjectionStateRepository(
            connection
        ),
        projection_versions=PostgresProjectionVersionRepository(
            connection
        ),
        operations_workspace=PostgresOperationsWorkspaceRepository(
            connection
        ),
    )

    return PostgresRuntimeRepositoryBundle(
        repositories=repositories,
        support=support,
        connection=connection,
    )


__all__ = [
    "PostgresRuntimeRepositoryBundle",
    "PostgresRuntimeSupportRepositories",
    "create_postgres_runtime_repository_bundle",
]
