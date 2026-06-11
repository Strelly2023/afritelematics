"""Contracts for constitutionally governed data decentralization."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class DataGovernanceViolation(RuntimeError):
    """Raised when decentralized data access breaks governance."""


class AccessMode(str, Enum):
    """Allowed cross-domain access modes."""

    API = "api"
    EVENT = "event"
    APPROVED_CONTRACT = "approved_contract"


@dataclass(frozen=True)
class DomainDataContract:
    """Declared data ownership for one AfriTech domain."""

    domain: str
    owned_resources: tuple[str, ...]
    write_authority: bool = True
    direct_database_sharing_allowed: bool = False

    def __post_init__(self) -> None:
        if not self.domain:
            raise DataGovernanceViolation("domain is required")
        if not self.owned_resources:
            raise DataGovernanceViolation("owned_resources are required")
        if len(set(self.owned_resources)) != len(self.owned_resources):
            raise DataGovernanceViolation("owned_resources must be unique")
        if self.direct_database_sharing_allowed is not False:
            raise DataGovernanceViolation("direct database sharing is forbidden")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "domain": self.domain,
            "owned_resources": self.owned_resources,
            "write_authority": self.write_authority,
            "direct_database_sharing_allowed": self.direct_database_sharing_allowed,
        }


@dataclass(frozen=True)
class DataAccessContract:
    """Approved cross-domain read/access path."""

    contract_id: str
    requester_domain: str
    owner_domain: str
    resource: str
    access_mode: AccessMode
    purpose: str
    metadata: tuple[tuple[str, object], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.contract_id:
            raise DataGovernanceViolation("contract_id is required")
        if not self.requester_domain:
            raise DataGovernanceViolation("requester_domain is required")
        if not self.owner_domain:
            raise DataGovernanceViolation("owner_domain is required")
        if not self.resource:
            raise DataGovernanceViolation("resource is required")
        if not self.purpose:
            raise DataGovernanceViolation("purpose is required")
        object.__setattr__(self, "metadata", _freeze_metadata(dict(self.metadata)))

    @property
    def direct_database_access(self) -> bool:
        return False

    def canonical_dict(self) -> dict[str, object]:
        return {
            "contract_id": self.contract_id,
            "requester_domain": self.requester_domain,
            "owner_domain": self.owner_domain,
            "resource": self.resource,
            "access_mode": self.access_mode.value,
            "purpose": self.purpose,
            "direct_database_access": self.direct_database_access,
            "metadata": dict(self.metadata),
        }


def _freeze_metadata(value: Mapping[str, object]) -> tuple[tuple[str, object], ...]:
    return tuple(sorted(value.items(), key=lambda item: str(item[0])))
