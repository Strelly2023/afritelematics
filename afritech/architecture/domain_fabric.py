from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_FABRIC_PATH = REPO_ROOT / "config" / "afritechnology" / "domain-fabric.yaml"
INTERNAL_ZONE_SUFFIX = "internal.afritechnology.com"


class DomainFabricError(ValueError):
    pass


def load_domain_fabric(path: str | Path = DOMAIN_FABRIC_PATH) -> dict[str, Any]:
    fabric_path = Path(path)
    if not fabric_path.exists():
        raise DomainFabricError(f"domain fabric not found: {fabric_path}")
    with fabric_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise DomainFabricError("domain fabric must be a mapping")
    return payload


def public_domain_records(fabric: dict[str, Any]) -> list[dict[str, Any]]:
    domains = fabric.get("domains", [])
    if not isinstance(domains, list):
        raise DomainFabricError("domains must be a list")
    return [record for record in domains if record.get("exposure") != "private"]


def private_domain_records(fabric: dict[str, Any]) -> list[dict[str, Any]]:
    domains = fabric.get("domains", [])
    if not isinstance(domains, list):
        raise DomainFabricError("domains must be a list")
    return [record for record in domains if record.get("exposure") == "private"]


def validate_domain_fabric(fabric: dict[str, Any]) -> None:
    wildcard_policy = fabric.get("wildcard_dns_policy")
    if wildcard_policy != "PRODUCTION_EXPLICIT_RECORDS_ONLY":
        raise DomainFabricError("wildcard DNS policy must remain PRODUCTION_EXPLICIT_RECORDS_ONLY")

    forbidden = fabric.get("forbidden", [])
    if not any(entry.get("host_pattern") == "*.afritechnology.com" for entry in forbidden if isinstance(entry, dict)):
        raise DomainFabricError("production wildcard DNS must remain forbidden")

    private_zone = fabric.get("private_hosted_zone", {})
    if private_zone.get("domain") != INTERNAL_ZONE_SUFFIX:
        raise DomainFabricError("private hosted zone must be internal.afritechnology.com")

    for record in public_domain_records(fabric):
        host = record.get("host", "")
        if not isinstance(host, str) or not host:
            raise DomainFabricError("each domain record must declare a host")
        if host.endswith(f".{INTERNAL_ZONE_SUFFIX}"):
            raise DomainFabricError(f"private host leaked into public records: {host}")
        if record.get("exposure") not in {"public", "public_authenticated", "public_controlled"}:
            raise DomainFabricError(f"unexpected public exposure class for {host}")

    for record in private_domain_records(fabric):
        host = record.get("host", "")
        if not host.endswith(f".{INTERNAL_ZONE_SUFFIX}"):
            raise DomainFabricError(f"private host must live in the private hosted zone: {host}")
        if record.get("exposure") != "private":
            raise DomainFabricError(f"private host must be marked private: {host}")


def summarize_domain_fabric(path: str | Path = DOMAIN_FABRIC_PATH) -> dict[str, Any]:
    fabric = load_domain_fabric(path)
    validate_domain_fabric(fabric)

    public_records = public_domain_records(fabric)
    private_records = private_domain_records(fabric)
    return {
        "schema": fabric.get("schema"),
        "canonical_domain": fabric.get("canonical_domain"),
        "wildcard_dns_policy": fabric.get("wildcard_dns_policy"),
        "unknown_host_policy": fabric.get("unknown_host_policy"),
        "public_host_count": len(public_records),
        "private_host_count": len(private_records),
        "public_categories": sorted({record.get("category") for record in public_records if record.get("category")}),
        "private_hosted_zone": fabric.get("private_hosted_zone", {}).get("domain"),
        "private_access_model": fabric.get("private_hosted_zone", {}).get("access_model"),
        "public_hosts": sorted(
            host for host in (record.get("host") for record in public_records) if isinstance(host, str)
        ),
    }
