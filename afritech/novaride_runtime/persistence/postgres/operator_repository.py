"""PostgreSQL persistence for NovaRide operator intervention commands.

NovaRide owns operator intervention workflow state.

Identity and authentication remain under NovaID.
Trust, risk, evidence policy and compliance remain under NovaTrust.
Financial/refund execution remains under NovaPay.

This repository deliberately persists only the active RuntimeRepositories
authority ``operator_commands``. Resilience and operations-workspace records
remain in their own persistence streams.
"""

from __future__ import annotations

from typing import Any, Mapping

from afritech.novaride_runtime.models import OperatorCommand
from afritech.novaride_runtime.persistence.postgres.base_repository import (
    PostgresAggregateRepository,
    SyncPostgresConnection,
)
from afritech.novaride_runtime.persistence.postgres.unit_of_work import (
    PostgresUnitOfWork,
    PostgresUnitOfWorkConfig,
)


def _encode_operator_command(
    command: OperatorCommand,
) -> Mapping[str, Any]:
    return {
        "command_id": command.id,
        "tenant_id": command.tenant_id,
        "organization_id": command.organization_id,
        "region_code": command.region_code,
        "command_type": command.command_type,
        "target_id": command.target_id,
        "reason": command.reason,
        "authority_decision": command.authority_decision,
        "evidence_reference": command.evidence_reference,
        "aggregate_version": command.aggregate_version,
        "created_at": command.created_at,
        "updated_at": command.updated_at,
    }


def _decode_operator_command(
    row: Mapping[str, Any],
) -> OperatorCommand:
    return OperatorCommand(
        id=str(row["command_id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(row["organization_id"]),
        region_code=str(row["region_code"]),
        aggregate_version=int(
            row.get("aggregate_version", 1)
        ),
        schema_version="2026.2",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        command_type=str(row["command_type"]),
        target_id=str(row["target_id"]),
        reason=str(row["reason"]),
        authority_decision=str(
            row["authority_decision"]
        ),
        evidence_reference=(
            None
            if row.get("evidence_reference") is None
            else str(row["evidence_reference"])
        ),
    )


class PostgresOperatorCommandRepository(
    PostgresAggregateRepository[OperatorCommand]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="operator_commands",
            id_column="command_id",
            to_record=_encode_operator_command,
            from_record=_decode_operator_command,
        )


__all__ = [
    "PostgresOperatorCommandRepository",
    "PostgresUnitOfWork",
    "PostgresUnitOfWorkConfig",
]
