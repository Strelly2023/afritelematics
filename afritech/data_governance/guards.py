"""Runtime-style guards for governed decentralized data access."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from afritech.data_governance.contracts import (
    AccessMode,
    DataAccessContract,
    DataGovernanceViolation,
)
from afritech.data_governance.ownership import owner_for_resource


@dataclass(frozen=True)
class DataWriteIntent:
    """Minimal write intent checked before domain-owned data mutation."""

    actor_domain: str
    owner_domain: str
    resource: str
    entity_id: str
    payload: Mapping[str, object]


def guard_owner_domain(entity: Mapping[str, object]) -> None:
    owner_domain = entity.get("owner_domain")
    entity_id = entity.get("id")
    if not isinstance(owner_domain, str) or not owner_domain.strip():
        raise DataGovernanceViolation("entity owner_domain is required")
    if not isinstance(entity_id, str) or not entity_id.strip():
        raise DataGovernanceViolation("entity id is required")


def guard_data_write(intent: DataWriteIntent) -> None:
    if owner_for_resource(intent.resource) != intent.owner_domain:
        raise DataGovernanceViolation("resource owner_domain mismatch")
    if intent.actor_domain != intent.owner_domain:
        raise DataGovernanceViolation("only owner domain may write owned data")
    guard_owner_domain(
        {
            "id": intent.entity_id,
            "owner_domain": intent.owner_domain,
        }
    )


def guard_cross_domain_access(contract: DataAccessContract) -> None:
    if owner_for_resource(contract.resource) != contract.owner_domain:
        raise DataGovernanceViolation("contract owner_domain does not own resource")
    if contract.access_mode not in {
        AccessMode.API,
        AccessMode.EVENT,
        AccessMode.APPROVED_CONTRACT,
    }:
        raise DataGovernanceViolation("unsupported cross-domain access mode")
    if contract.direct_database_access:
        raise DataGovernanceViolation("direct cross-domain database access is forbidden")
