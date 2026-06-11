"""Registry-level assertions for governed decentralized data architecture."""

from __future__ import annotations

from afritech.data_governance.contracts import DataGovernanceViolation
from afritech.data_governance.ownership import DATA_OWNERSHIP_REGISTRY


INV_DATA_001 = (
    "No domain may directly read or write another domain database table; "
    "cross-domain access must use declared APIs, events, or approved contracts."
)

DATA_DECENTRALIZATION_STATUS = "GOVERNED_DECENTRALIZATION_DEFINED"


def validate_data_governance_registry() -> bool:
    seen_resources: set[str] = set()
    seen_domains: set[str] = set()

    for contract in DATA_OWNERSHIP_REGISTRY:
        if contract.domain in seen_domains:
            raise DataGovernanceViolation(f"duplicate data domain: {contract.domain}")
        seen_domains.add(contract.domain)
        if contract.direct_database_sharing_allowed:
            raise DataGovernanceViolation("direct database sharing is forbidden")

        for resource in contract.owned_resources:
            if resource in seen_resources:
                raise DataGovernanceViolation(f"duplicate owned resource: {resource}")
            seen_resources.add(resource)

    if "AfriPay" not in seen_domains:
        raise DataGovernanceViolation("AfriPay evidence domain must be declared")
    return True
