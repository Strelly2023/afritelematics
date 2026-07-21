"""Governed NovaPay platform domains."""

from .repository import (
    NovaPayRecord,
    NovaPayRepository,
    PostgresNovaPayRepository,
    build_repository_from_environment,
    validate_database_runtime,
)
from .portal_suite import NovaPortalSuite
from .migration import migrate_legacy_monetary_state
from .service import NovaPayEcosystem
from .surfaces import build_app_surfaces, build_trust_surfaces
from .ecosystem_contract import novapay_ecosystem_contract

__all__ = [
    "NovaPayEcosystem",
    "NovaPayRecord",
    "NovaPayRepository",
    "PostgresNovaPayRepository",
    "NovaPortalSuite",
    "migrate_legacy_monetary_state",
    "build_repository_from_environment",
    "build_app_surfaces",
    "build_trust_surfaces",
    "novapay_ecosystem_contract",
    "validate_database_runtime",
]
