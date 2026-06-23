"""Persistence adapters for NovaTech core platform receipts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from afritech.core_platform.models import CorePlatformFlowResult, TrustReceipt
from afritech.core_platform.orm import CoreTrustPacketRecord


class CorePlatformStore(Protocol):
    def save_flow(self, result: CorePlatformFlowResult) -> None:
        ...

    def get_trust_packet(self, identifier: str) -> dict[str, object] | None:
        ...


@dataclass
class InMemoryCorePlatformStore:
    by_trust_id: dict[str, dict[str, object]] = field(default_factory=dict)
    by_receipt_id: dict[str, dict[str, object]] = field(default_factory=dict)

    def save_flow(self, result: CorePlatformFlowResult) -> None:
        packet = result.canonical()
        self.by_trust_id[result.trust.trust_id] = packet
        if result.payment is not None:
            self.by_receipt_id[result.payment.receipt_id] = packet

    def save_trust_receipt(self, receipt: TrustReceipt) -> None:
        packet = {"trust": receipt.canonical(), "payment": None}
        self.by_trust_id[receipt.trust_id] = packet

    def get_trust_packet(self, identifier: str) -> dict[str, object] | None:
        return self.by_trust_id.get(identifier) or self.by_receipt_id.get(identifier)


class PostgresCorePlatformStore:
    """PostgreSQL-backed receipt store using psycopg.

    The adapter creates a compact JSONB table for core proof packets. It keeps
    the schema intentionally narrow so the deterministic models remain the
    contract and PostgreSQL remains the durable storage boundary.
    """

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS novatech_core_trust_packets (
                    id TEXT PRIMARY KEY,
                    receipt_id TEXT,
                    organization_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    packet JSONB NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_novatech_core_trust_receipt
                ON novatech_core_trust_packets(receipt_id)
                """
            )

    def save_flow(self, result: CorePlatformFlowResult) -> None:
        record = CoreTrustPacketRecord.from_flow(result)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO novatech_core_trust_packets
                    (id, receipt_id, organization_id, event_type, packet)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    receipt_id = EXCLUDED.receipt_id,
                    organization_id = EXCLUDED.organization_id,
                    event_type = EXCLUDED.event_type,
                    packet = EXCLUDED.packet
                """,
                record.insert_params(),
            )

    def get_trust_packet(self, identifier: str) -> dict[str, object] | None:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, receipt_id, organization_id, event_type, packet
                FROM novatech_core_trust_packets
                WHERE id = %s OR receipt_id = %s
                LIMIT 1
                """,
                (identifier, identifier),
            ).fetchall()
        if not rows:
            return None
        return dict(CoreTrustPacketRecord.from_row(rows[0]).packet)

    def _connect(self):
        import psycopg

        return psycopg.connect(self.dsn)
