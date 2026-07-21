"""NovaPay legacy monetary migration helpers."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
from typing import Any, Protocol

from .repository import NovaPayRecord


class ReadableNovaPayRepository(Protocol):
    def table_names(self) -> tuple[str, ...]: ...

    def list(
        self,
        table_name: str,
        *,
        organization_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[NovaPayRecord]: ...


class WritableNovaPayRepository(Protocol):
    def upsert(
        self,
        table_name: str,
        *,
        record_id: str,
        organization_id: str,
        status: str,
        payload: dict[str, Any],
    ) -> NovaPayRecord: ...


def _money(value: Any) -> Decimal:
    return Decimal(str(value))


def _fingerprint(record: NovaPayRecord) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "record_id": record.record_id,
                "organization_id": record.organization_id,
                "status": record.status,
                "payload": record.payload,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def migrate_legacy_monetary_state(
    source: ReadableNovaPayRepository,
    target: WritableNovaPayRepository,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    inventory: dict[str, int] = {}
    source_hasher = hashlib.sha256()
    ledger_totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"debit": Decimal("0"), "credit": Decimal("0")}
    )
    migrated = 0
    for table_name in source.table_names():
        records = source.list(table_name, limit=100_000)
        inventory[table_name] = len(records)
        for record in records:
            source_hasher.update(_fingerprint(record).encode("utf-8"))
            payload = dict(record.payload)
            if table_name == "novapay_ledger_entries":
                currency = str(payload.get("currency", ""))
                entry_type = str(payload.get("entry_type", "")).lower()
                if entry_type in {"debit", "credit"} and currency:
                    ledger_totals[currency][entry_type] += _money(payload.get("amount", "0"))
            if not dry_run:
                target.upsert(
                    table_name,
                    record_id=record.record_id,
                    organization_id=record.organization_id,
                    status=record.status,
                    payload=payload,
                )
            migrated += 1

    mismatches: dict[str, dict[str, str]] = {}
    for currency, totals in ledger_totals.items():
        if totals["debit"] != totals["credit"]:
            mismatches[currency] = {
                "debit": f"{totals['debit']:.2f}",
                "credit": f"{totals['credit']:.2f}",
            }
    if mismatches:
        raise ValueError("migration_totals_do_not_reconcile")

    return {
        "dry_run": dry_run,
        "inventory": inventory,
        "ledger_totals": {
            currency: {
                "debit": f"{totals['debit']:.2f}",
                "credit": f"{totals['credit']:.2f}",
                "balanced": totals["debit"] == totals["credit"],
            }
            for currency, totals in ledger_totals.items()
        },
        "source_hash": source_hasher.hexdigest(),
        "migrated_records": migrated,
    }
