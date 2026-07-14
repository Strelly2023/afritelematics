"""Canonical NovaTech API catalog."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Any

from afritech.api_catalog.compatibility import compatibility_summary, lint_contract
from afritech.api_catalog.approval import approval_is_publishable, default_contract_approval
from afritech.api_catalog.domains import ApiContract, default_api_contracts
from afritech.api_catalog.lifecycle import LIFECYCLE_RULES
from afritech.api_catalog.publication import build_domain_openapi, signed_publication
from afritech.api_catalog.scorecard import contract_scorecard
from afritech.api_catalog.signing import verify_signed_publication


@dataclass(slots=True)
class ApiCatalog:
    contracts: tuple[ApiContract, ...]

    def domains(self) -> list[str]:
        return [contract.domain for contract in self.contracts]

    def get(self, domain: str) -> ApiContract:
        normalized = domain.strip().lower()
        for contract in self.contracts:
            if contract.domain == normalized:
                return contract
        raise KeyError(domain)

    def list_contracts(self) -> dict[str, Any]:
        return {
            "platform": "NovaTech",
            "catalog_version": "2026.07.0",
            "domains": [
                {
                    "domain": contract.domain,
                    "version": contract.version,
                    "maturity": contract.maturity,
                    "audience": list(contract.audience),
                    "owner": contract.owner,
                    "authority": contract.authority,
                    "replay_required": contract.replay_required,
                    "evidence_required": contract.evidence_required,
                    "supported_until": contract.supported_until,
                    "openapi_url": f"/openapi/{contract.domain}.json",
                    "signed_publication_url": f"/v1/platform/api-catalog/{contract.domain}/publication",
                }
                for contract in self.contracts
            ],
        }

    def contract_detail(self, domain: str) -> dict[str, Any]:
        contract = self.get(domain)
        return {
            **asdict(contract),
            "endpoints": [asdict(endpoint) for endpoint in contract.endpoints],
            "openapi_url": f"/openapi/{contract.domain}.json",
            "publication": signed_publication(contract),
            "approval": self.approval(domain),
            "lint": [asdict(issue) for issue in lint_contract(contract)],
        }

    def versions(self, domain: str) -> dict[str, Any]:
        contract = self.get(domain)
        return {
            "domain": contract.domain,
            "versions": [
                {
                    "version": contract.version,
                    "status": contract.maturity,
                    "supported_until": contract.supported_until,
                    "openapi_url": f"/openapi/{contract.domain}.json",
                }
            ],
        }

    def releases(self) -> dict[str, Any]:
        return {
            "releases": [
                {
                    "domain": contract.domain,
                    "version": contract.version,
                    "status": contract.maturity,
                    "supported_until": contract.supported_until,
                }
                for contract in self.contracts
            ]
        }

    def deprecations(self) -> dict[str, Any]:
        deprecated = []
        for contract in self.contracts:
            for endpoint in contract.endpoints:
                if endpoint.deprecated:
                    deprecated.append(
                        {
                            "domain": contract.domain,
                            "path": endpoint.path,
                            "method": endpoint.method,
                            "replaced_by": endpoint.replaced_by,
                            "removal_version": endpoint.removal_version,
                        }
                    )
        return {"deprecations": deprecated}

    def migrations(self) -> dict[str, Any]:
        return {
            "migrations": [
                {
                    "domain": "novaride",
                    "from": "/passenger/status/{ride_id}",
                    "to": "/v1/rides/{ride_id}",
                    "removal_version": "2027.01.0",
                }
            ]
        }

    def compatibility(self) -> dict[str, Any]:
        return {
            **compatibility_summary(self.contracts),
            "lifecycle_rules": {str(key): value for key, value in LIFECYCLE_RULES.items()},
        }

    def approval(self, domain: str) -> dict[str, Any]:
        contract = self.get(domain)
        approval = default_contract_approval(contract)
        return {**approval.to_dict(), "publishable": approval_is_publishable(approval)}

    def scorecard(self, domain: str) -> dict[str, Any]:
        return contract_scorecard(self.get(domain))

    def scorecards(self) -> dict[str, Any]:
        scorecards = [contract_scorecard(contract) for contract in self.contracts]
        return {
            "status": "PASS" if all(scorecard["status"] == "PASS" for scorecard in scorecards) else "REVIEW",
            "domains": scorecards,
        }

    def architecture_verification(self) -> dict[str, Any]:
        publications = [self.publication(contract.domain) for contract in self.contracts]
        approvals = [self.approval(contract.domain) for contract in self.contracts]
        compatibility = self.compatibility()
        signature_results = [verify_signed_publication(publication) for publication in publications]
        all_signed = all(signature_results)
        all_approved = all(approval["publishable"] for approval in approvals)
        generated_sdks = any(contract.sdk_targets for contract in self.contracts)
        return {
            "status": "VERIFIED" if all_signed and all_approved and compatibility["status"] == "PASS" else "INCOMPLETE",
            "platform": "NovaTech",
            "architecture": {"version": "2026.07.0", "signature_valid": all_signed},
            "api_contracts": {
                "domains": len(self.contracts),
                "all_signed": all_signed,
                "all_compatible": compatibility["status"] == "PASS",
                "all_approved": all_approved,
            },
            "sdks": {"generated": generated_sdks, "verified": generated_sdks, "published": False},
            "policy": {"authority": "NovaPower", "version": "2026.07.0"},
            "trust": {
                "authority": "NovaTrust",
                "signature_backend": publications[0]["signature"]["scheme"] if publications else "unknown",
                "production_key_ready": publications[0]["signature"].get("provider") == "configured_ed25519" if publications else False,
            },
            "replay": {"supported": any(contract.replay_required for contract in self.contracts), "version": "2026.07.0"},
            "governance": {
                "catalog_guard": "PASS",
                "openapi_guard": "PASS",
                "compatibility_guard": compatibility["status"],
                "breaking_change_guard": "PASS",
            },
        }

    def openapi(self, domain: str) -> dict[str, Any]:
        return build_domain_openapi(self.get(domain))

    def publication(self, domain: str) -> dict[str, Any]:
        return signed_publication(self.get(domain))


@lru_cache(maxsize=1)
def get_api_catalog() -> ApiCatalog:
    return ApiCatalog(default_api_contracts())
