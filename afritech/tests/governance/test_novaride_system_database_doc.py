from __future__ import annotations

from pathlib import Path


DOC = Path(__file__).resolve().parents[3] / "docs/architecture/NOVARIDE_SYSTEM_DATABASE_V1.md"


def test_novaride_system_database_doc_exists() -> None:
    text = DOC.read_text(encoding="utf-8")
    for required in (
        "STATUS: BOUNDED OPERATIONAL DATABASE CONTRACT",
        "CLASSIFICATION: ISOLATED PRODUCT DATA DESIGN SURFACE",
        "GOVERNANCE MODE: PRESERVE OR ISOLATE",
        "Apps = Interface",
        "Platform = Authority",
    ):
        assert required in text


def test_novaride_system_database_doc_covers_core_tables_and_contracts() -> None:
    text = DOC.read_text(encoding="utf-8")
    for required in (
        "organizations",
        "accounts",
        "subscriptions",
        "catalog_features",
        "feature_flags",
        "audit_events",
        "notifications",
        "integrations",
        "rides",
        "wallets",
        "transactions",
        "driver_presence",
        "dispatch_assignments",
        "external_payment_authorizations",
        "external_payment_captures",
        "event_stream_events",
        "tenant isolation",
        "deterministic dispatch",
        "payment provider",
    ):
        assert required in text

