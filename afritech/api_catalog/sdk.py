"""SDK compatibility metadata derived from API contracts."""

from __future__ import annotations

from dataclasses import dataclass

from afritech.api_catalog.domains import ApiContract


@dataclass(frozen=True, slots=True)
class SdkCompatibility:
    sdk_name: str
    sdk_version: str
    contract_version: str
    supported_api_versions: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "sdk_version": self.sdk_version,
            "contract_version": self.contract_version,
            "supported_api_versions": list(self.supported_api_versions),
        }


def sdk_compatibility(contract: ApiContract) -> dict[str, dict[str, object]]:
    major_minor = ".".join(contract.version.split(".")[:2])
    return {
        target: SdkCompatibility(
            sdk_name=target,
            sdk_version=contract.version,
            contract_version=contract.version,
            supported_api_versions=(major_minor, contract.version),
        ).to_dict()
        for target in contract.sdk_targets
    }
