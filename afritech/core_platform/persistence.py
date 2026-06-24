"""Persistence adapters for NovaTech core platform receipts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from afritech.core_platform.models import CorePlatformFlowResult, TrustReceipt
from afritech.core_platform.orm import CoreTrustPacketRecord
from afritech.core_platform.signing import sign_packet


class CorePlatformStore(Protocol):
    def save_flow(self, result: CorePlatformFlowResult) -> None:
        ...

    def get_trust_packet(self, identifier: str) -> dict[str, object] | None:
        ...


@dataclass
class InMemoryCorePlatformStore:
    by_trust_id: dict[str, dict[str, object]] = field(default_factory=dict)
    by_receipt_id: dict[str, dict[str, object]] = field(default_factory=dict)
    by_intent_id: dict[tuple[str, str], dict[str, object]] = field(default_factory=dict)
    signatures: dict[str, dict[str, str]] = field(default_factory=dict)
    imported_envelopes: set[str] = field(default_factory=set)
    webhook_events: set[tuple[str, str]] = field(default_factory=set)

    def save_flow(self, result: CorePlatformFlowResult) -> None:
        packet = result.canonical()
        self.by_trust_id[result.trust.trust_id] = packet
        intent_id = str(result.trust.packet.get("payment_intent", {}).get("intent_id", ""))
        if intent_id:
            self.by_intent_id[(result.trust.organization_id, intent_id)] = packet
        self.signatures[result.trust.trust_id] = sign_packet(packet).canonical()
        if result.payment is not None:
            self.by_receipt_id[result.payment.receipt_id] = packet

    def save_trust_receipt(self, receipt: TrustReceipt) -> None:
        packet = {"trust": receipt.canonical(), "payment": None}
        self.by_trust_id[receipt.trust_id] = packet

    def get_trust_packet(self, identifier: str) -> dict[str, object] | None:
        return self.by_trust_id.get(identifier) or self.by_receipt_id.get(identifier)

    def get_signature(self, identifier: str) -> dict[str, str] | None:
        packet = self.get_trust_packet(identifier)
        if packet is None:
            return None
        trust = packet.get("trust")
        trust_id = (
            str(trust.get("trust_id"))
            if isinstance(trust, Mapping) and trust.get("trust_id")
            else identifier
        )
        return self.signatures.get(trust_id)

    def get_by_intent(
        self,
        organization_id: str,
        intent_id: str,
    ) -> dict[str, object] | None:
        return self.by_intent_id.get((organization_id, intent_id))

    def save_imported_packet(
        self,
        *,
        trust_id: str,
        packet: Mapping[str, Any],
        signature: Mapping[str, str],
        source_node: str,
        envelope_id: str,
        imported_at: str,
    ) -> bool:
        if envelope_id in self.imported_envelopes:
            return False
        existing = self.by_trust_id.get(trust_id)
        if existing is not None and existing != dict(packet):
            raise ValueError("trust_id_conflict")
        self.imported_envelopes.add(envelope_id)
        self.by_trust_id[trust_id] = dict(packet)
        self.signatures[trust_id] = dict(signature)
        return True

    def find_payment(
        self,
        *,
        payment_id: str | None,
        provider_reference: str,
    ) -> dict[str, object] | None:
        for packet in self.by_trust_id.values():
            payment = packet.get("payment")
            if not isinstance(payment, Mapping):
                continue
            if payment_id and payment.get("payment_id") == payment_id:
                return dict(payment)
            if (
                provider_reference
                and payment.get("provider_reference") == provider_reference
            ):
                return dict(payment)
        return None

    def claim_webhook_event(
        self,
        *,
        provider: str,
        event_id: str,
        payment_id: str | None = None,
        provider_reference: str = "",
        settlement_status: str = "received",
        payload: Mapping[str, Any] | None = None,
    ) -> bool:
        key = (provider, event_id)
        if key in self.webhook_events:
            return False
        self.webhook_events.add(key)
        return True


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
                ALTER TABLE novatech_core_trust_packets
                    ADD COLUMN IF NOT EXISTS intent_id TEXT,
                    ADD COLUMN IF NOT EXISTS signature JSONB,
                    ADD COLUMN IF NOT EXISTS source_node TEXT NOT NULL
                        DEFAULT 'novatech-primary',
                    ADD COLUMN IF NOT EXISTS imported BOOLEAN NOT NULL DEFAULT FALSE,
                    ADD COLUMN IF NOT EXISTS envelope_id TEXT,
                    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_novatech_core_trust_receipt
                ON novatech_core_trust_packets(receipt_id)
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_novatech_core_trust_intent
                ON novatech_core_trust_packets(organization_id, intent_id)
                WHERE intent_id IS NOT NULL
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_novatech_core_trust_envelope
                ON novatech_core_trust_packets(envelope_id)
                WHERE envelope_id IS NOT NULL
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS novatech_payment_webhook_events (
                    event_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    payment_id TEXT,
                    provider_reference TEXT,
                    settlement_status TEXT NOT NULL,
                    payload JSONB NOT NULL,
                    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (provider, event_id)
                )
                """
            )

    def save_flow(self, result: CorePlatformFlowResult) -> None:
        record = CoreTrustPacketRecord.from_flow(result)
        packet = dict(record.packet)
        signature = sign_packet(packet).canonical()
        intent_id = str(result.trust.packet.get("payment_intent", {}).get("intent_id", ""))
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO novatech_core_trust_packets
                    (
                        id, receipt_id, organization_id, event_type, packet,
                        intent_id, signature, source_node, imported
                    )
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'novatech-primary', FALSE)
                ON CONFLICT (id) DO UPDATE SET
                    receipt_id = EXCLUDED.receipt_id,
                    organization_id = EXCLUDED.organization_id,
                    event_type = EXCLUDED.event_type,
                    packet = EXCLUDED.packet,
                    intent_id = EXCLUDED.intent_id,
                    signature = EXCLUDED.signature
                """,
                (
                    record.id,
                    record.receipt_id,
                    record.organization_id,
                    record.event_type,
                    json.dumps(packet, sort_keys=True),
                    intent_id or None,
                    json.dumps(signature, sort_keys=True),
                ),
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

    def get_signature(self, identifier: str) -> dict[str, str] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT signature
                FROM novatech_core_trust_packets
                WHERE id = %s OR receipt_id = %s
                LIMIT 1
                """,
                (identifier, identifier),
            ).fetchone()
        if not row or row[0] is None:
            return None
        return dict(row[0]) if not isinstance(row[0], str) else json.loads(row[0])

    def get_by_intent(
        self,
        organization_id: str,
        intent_id: str,
    ) -> dict[str, object] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT packet
                FROM novatech_core_trust_packets
                WHERE organization_id = %s AND intent_id = %s
                LIMIT 1
                """,
                (organization_id, intent_id),
            ).fetchone()
        if not row:
            return None
        return dict(row[0]) if not isinstance(row[0], str) else json.loads(row[0])

    def save_imported_packet(
        self,
        *,
        trust_id: str,
        packet: Mapping[str, Any],
        signature: Mapping[str, str],
        source_node: str,
        envelope_id: str,
        imported_at: str,
    ) -> bool:
        trust = packet.get("trust")
        organization_id = (
            str(trust.get("organization_id", "federated"))
            if isinstance(trust, Mapping)
            else "federated"
        )
        event_type = (
            str(trust.get("event_type", "federation.trust.imported"))
            if isinstance(trust, Mapping)
            else "federation.trust.imported"
        )
        receipt_id = None
        payment = packet.get("payment")
        if isinstance(payment, Mapping) and payment.get("receipt_id"):
            receipt_id = str(payment["receipt_id"])

        with self._connect() as conn:
            existing = conn.execute(
                "SELECT packet, envelope_id FROM novatech_core_trust_packets WHERE id = %s",
                (trust_id,),
            ).fetchone()
            if existing:
                existing_packet = (
                    dict(existing[0])
                    if not isinstance(existing[0], str)
                    else json.loads(existing[0])
                )
                if existing_packet != dict(packet):
                    raise ValueError("trust_id_conflict")
                return False
            cursor = conn.execute(
                """
                INSERT INTO novatech_core_trust_packets
                    (
                        id, receipt_id, organization_id, event_type, packet,
                        signature, source_node, imported, envelope_id, created_at
                    )
                VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (
                    trust_id,
                    receipt_id,
                    organization_id,
                    event_type,
                    json.dumps(dict(packet), sort_keys=True),
                    json.dumps(dict(signature), sort_keys=True),
                    source_node,
                    envelope_id,
                    imported_at,
                ),
            )
            if cursor.rowcount == 1:
                return True
            concurrent = conn.execute(
                "SELECT packet FROM novatech_core_trust_packets WHERE id = %s",
                (trust_id,),
            ).fetchone()
            if concurrent:
                concurrent_packet = (
                    dict(concurrent[0])
                    if not isinstance(concurrent[0], str)
                    else json.loads(concurrent[0])
                )
                if concurrent_packet != dict(packet):
                    raise ValueError("trust_id_conflict")
            return False

    def find_payment(
        self,
        *,
        payment_id: str | None,
        provider_reference: str,
    ) -> dict[str, object] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT payment
                FROM (
                    SELECT packet->'payment' AS payment
                    FROM novatech_core_trust_packets
                ) payments
                WHERE
                    (%s IS NOT NULL AND payment->>'payment_id' = %s)
                    OR
                    (%s <> '' AND payment->>'provider_reference' = %s)
                LIMIT 1
                """,
                (
                    payment_id,
                    payment_id,
                    provider_reference,
                    provider_reference,
                ),
            ).fetchone()
        if not row or row[0] is None:
            return None
        return dict(row[0]) if not isinstance(row[0], str) else json.loads(row[0])

    def claim_webhook_event(
        self,
        *,
        provider: str,
        event_id: str,
        payment_id: str | None = None,
        provider_reference: str = "",
        settlement_status: str = "received",
        payload: Mapping[str, Any] | None = None,
    ) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO novatech_payment_webhook_events
                    (
                        provider, event_id, payment_id, provider_reference,
                        settlement_status, payload
                    )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (provider, event_id) DO NOTHING
                """,
                (
                    provider,
                    event_id,
                    payment_id,
                    provider_reference,
                    settlement_status,
                    json.dumps(dict(payload or {}), sort_keys=True),
                ),
            )
            return cursor.rowcount == 1

    def _connect(self):
        import psycopg

        return psycopg.connect(self.dsn)
