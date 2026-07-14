"""Guard that verifies generated domain OpenAPI specs carry governance metadata."""

from __future__ import annotations

import sys

from afritech.api_catalog.registry import get_api_catalog


REQUIRED_OPERATION_EXTENSIONS = {
    "x-novatech-domain",
    "x-novatech-maturity",
    "x-novatech-audience",
    "x-novatech-authority",
    "x-novatech-evidence",
    "x-novatech-risk",
}


def validate_openapi_governance() -> list[str]:
    catalog = get_api_catalog()
    issues: list[str] = []
    for domain in catalog.domains():
        spec = catalog.openapi(domain)
        if spec.get("x-novatech-domain") != domain:
            issues.append(f"missing_domain_extension:{domain}")
        schemas = spec.get("components", {}).get("schemas", {})
        for schema_name in ("NovaTechEnvelope", "NovaTechErrorEnvelope"):
            if schema_name not in schemas:
                issues.append(f"missing_schema:{domain}:{schema_name}")
        for path, path_item in spec.get("paths", {}).items():
            for method, operation in path_item.items():
                missing = sorted(REQUIRED_OPERATION_EXTENSIONS - set(operation))
                if missing:
                    issues.append(f"missing_operation_extensions:{domain}:{method.upper()}:{path}:{','.join(missing)}")
                if operation.get("deprecated") and not operation.get("x-replaced-by"):
                    issues.append(f"deprecated_without_replacement:{domain}:{method.upper()}:{path}")
    return issues


def main() -> int:
    issues = validate_openapi_governance()
    if issues:
        for issue in issues:
            print(issue)
        return 1
    print("openapi_governance_guard=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
