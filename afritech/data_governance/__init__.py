"""Governed decentralized data ownership surface."""

from afritech.data_governance.contracts import (
    AccessMode,
    DataAccessContract,
    DataGovernanceViolation,
    DomainDataContract,
)
from afritech.data_governance.guards import (
    guard_cross_domain_access,
    guard_data_write,
    guard_owner_domain,
)
from afritech.data_governance.ownership import (
    DATA_OWNERSHIP_REGISTRY,
    owner_for_resource,
    resources_for_domain,
)
from afritech.data_governance.registry import (
    DATA_DECENTRALIZATION_STATUS,
    INV_DATA_001,
    validate_data_governance_registry,
)

__all__ = [
    "AccessMode",
    "DATA_DECENTRALIZATION_STATUS",
    "DATA_OWNERSHIP_REGISTRY",
    "DataAccessContract",
    "DataGovernanceViolation",
    "DomainDataContract",
    "INV_DATA_001",
    "guard_cross_domain_access",
    "guard_data_write",
    "guard_owner_domain",
    "owner_for_resource",
    "resources_for_domain",
    "validate_data_governance_registry",
]
