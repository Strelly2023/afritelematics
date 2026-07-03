from __future__ import annotations

from architecture_validator.model import RuleResult, pass_or_fail
from architecture_validator.scanners.files import read_text


def _route_literal(endpoint: str) -> str:
    return endpoint.removeprefix("/v1")


def check_api_contracts(config: dict[str, object]) -> RuleResult:
    issues: list[str] = []
    docs = read_text(str(config["docs_path"]))
    api_source = read_text(str(config["api_source_path"]))
    dashboard_source = read_text(str(config["dashboard_source_path"]))

    for endpoint in config.get("api_endpoints", []):
        endpoint = str(endpoint)
        if endpoint not in docs:
            issues.append(f"Documented Public APIs section missing endpoint: {endpoint}")
        route = _route_literal(endpoint)
        if route not in api_source and endpoint not in api_source:
            issues.append(f"API source does not expose documented endpoint: {endpoint}")
        if endpoint not in dashboard_source and endpoint != "/v1/novaride/{surface_key}/workspace":
            issues.append(f"Dashboard does not consume/declare endpoint: {endpoint}")

    for required in (
        "All API behavior SHALL be derived from versioned contracts.",
        "Clients MUST NOT rely on undocumented behavior.",
        "Any response shape, field, or workflow not defined in the contract is",
    ):
        if required not in docs:
            issues.append(f"Missing API contract enforcement rule: {required}")

    return pass_or_fail("API Contracts", issues)
