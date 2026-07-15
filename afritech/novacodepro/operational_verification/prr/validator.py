from __future__ import annotations

from .models import PRRPackage


def validate_prr_package(package: PRRPackage, production: bool = False) -> dict[str, object]:
    dev_signature_blocks = production and package.signature_assurance == "DEVELOPMENT_ONLY"
    return {
        "valid": not dev_signature_blocks and all(domain.status == "PASS" for domain in package.domains),
        "ga_allowed": False,
        "real_payments_enabled": False,
        "development_signature_blocks_production": dev_signature_blocks,
    }
