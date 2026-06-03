import json
import pytest
from django.db import connection, transaction

from afritech.models.audit_log import AuditLog
from afritech.audit.chain_validator import ChainValidator, ChainValidationError


# =====================================================
# ✅ TEST 1 — AUDIT CHAIN INTEGRITY
# =====================================================

@pytest.mark.django_db
def test_audit_chain_integrity():
    AuditLog.objects.create(payload={"a": 1}, epoch=1)
    AuditLog.objects.create(payload={"b": 2}, epoch=2)
    AuditLog.objects.create(payload={"c": 3}, epoch=3)

    logs = list(AuditLog.objects.order_by("timestamp"))

    assert ChainValidator.validate_chain(logs) is True


# =====================================================
# ✅ TEST 2 — ORM TAMPER PREVENTION
# =====================================================

@pytest.mark.django_db
def test_tamper_detection():
    log1 = AuditLog.objects.create(payload={"a": 1}, epoch=1)
    log2 = AuditLog.objects.create(payload={"b": 2}, epoch=2)

    log2.entry_hash = "fake_hash"

    with pytest.raises(ValueError):
        log2.save(update_fields=["entry_hash"])


# =====================================================
# ✅ TEST 3 — DB-LEVEL TAMPER DETECTION (RAW)
# =====================================================

class DummyEntry:
    """
    Adapter for raw DB rows → compatible with ChainValidator.
    Ensures payload is always a dict (canonical requirement).
    """

    def __init__(self, row):
        self.id = row["id"]
        self.previous_hash = row["previous_hash"]
        self.entry_hash = row["entry_hash"]

        # ✅ FIX: normalize payload
        payload = row["payload"]

        if isinstance(payload, str):
            try:
                self.payload = json.loads(payload)
            except Exception:
                # corrupted payload → force failure
                raise ValueError("INVALID_PAYLOAD_IN_DB")
        else:
            self.payload = payload


@pytest.mark.django_db(transaction=True)
def test_forced_tamper_detection():
    log1 = AuditLog.objects.create(payload={"a": 1}, epoch=1)
    log2 = AuditLog.objects.create(payload={"b": 2}, epoch=2)

    # ✅ Tamper DB directly (correct UUID format for SQLite)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE afritech_auditlog SET entry_hash = %s WHERE id = %s",
            ["fake_hash", log2.id.hex],  # ✅ critical fix
        )
        assert cursor.rowcount == 1, "Tampering update failed"

    transaction.commit()

    # ✅ Read raw DB values
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, previous_hash, entry_hash, payload
            FROM afritech_auditlog
            ORDER BY timestamp
            """
        )

        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # ✅ Wrap rows into validator-compatible objects
    logs = [DummyEntry(row) for row in rows]

    # ✅ Must detect corruption
    with pytest.raises(ChainValidationError):
        ChainValidator.validate_chain(logs)
