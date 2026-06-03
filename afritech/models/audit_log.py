import uuid
from django.db import models
from django.utils import timezone

from afritech.audit.merkle import MerkleTree
from afritech.audit.hash_engine import HashEngine
from afritech.audit.chain_validator import ChainValidator
from afritech.guards.audit_chain_guard import AuditChainGuard


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    payload = models.JSONField()

    previous_hash = models.CharField(max_length=64, null=True, blank=True)
    entry_hash = models.CharField(max_length=64, editable=False)

    timestamp = models.DateTimeField(default=timezone.now)
    epoch = models.IntegerField()

    status = models.CharField(max_length=20, default="VALID")
    invalid_reason = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["timestamp", "id"]
        indexes = [
            models.Index(fields=["timestamp"]),
            models.Index(fields=["epoch"]),
            models.Index(fields=["entry_hash"]),
        ]

    def __str__(self):
        return f"AuditLog<{self.id}>"

    # =====================================================
    # ✅ SAVE OVERRIDE (ADR‑0013 ENFORCEMENT)
    # =====================================================

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        if is_new:
            self._apply_chain_logic()
        else:
            # Prevent mutation (immutability rule)
            if self.has_hash_fields_changed():
                raise ValueError("IMMUTABLE_AUDIT_ENTRY_VIOLATION")

        super().save(*args, **kwargs)

    # =====================================================
    # ✅ CHANGE DETECTION
    # =====================================================

    def has_hash_fields_changed(self) -> bool:
        if not self.pk:
            return False

        try:
            original = AuditLog.objects.get(pk=self.pk)
        except AuditLog.DoesNotExist:
            return False

        protected_fields = [
            "payload",
            "previous_hash",
            "entry_hash",
            "epoch",
        ]

        for field in protected_fields:
            if getattr(original, field) != getattr(self, field):
                return True

        return False

    # =====================================================
    # ✅ CHAIN LOGIC
    # =====================================================

    def _apply_chain_logic(self):
        last_entry = self._get_last_valid_entry()

        # Previous hash
        self.previous_hash = last_entry.entry_hash if last_entry else None

        # Compute entry hash
        self.entry_hash = HashEngine.compute_hash(
            previous_hash=self.previous_hash,
            payload=self.payload
        )

        # Guard enforcement
        AuditChainGuard.validate_pre_insert(self, last_entry)

        # Chain validation
        ChainValidator.validate_append(last_entry, self)

    # =====================================================
    # ✅ QUERY HELPERS
    # =====================================================

    @staticmethod
    def _get_last_valid_entry():
        return (
            AuditLog.objects
            .filter(status="VALID")
            .order_by("-timestamp", "-id")
            .first()
        )

    # =====================================================
    # ✅ CHAIN VALIDATION
    # =====================================================

    @staticmethod
    def validate_full_chain():
        logs = list(
            AuditLog.objects
            .filter(status="VALID")
            .order_by("timestamp", "id")
        )
        return ChainValidator.validate_chain(logs)

    # =====================================================
    # ✅ MERKLE ROOT COMPUTATION ✅ (FIXED)
    # =====================================================

    @staticmethod
    def compute_merkle_root():
        """
        Computes Merkle root for all VALID audit entries.
        """

        logs = (
            AuditLog.objects
            .filter(status="VALID")
            .order_by("timestamp", "id")
        )

        leaf_hashes = [log.entry_hash for log in logs]

        if not leaf_hashes:
            return None

        tree = MerkleTree(leaf_hashes)
        return tree.get_root()

    # =====================================================
    # ✅ SAFE CREATION API
    # =====================================================

    @classmethod
    def create_entry(cls, payload: dict, epoch: int):
        entry = cls(payload=payload, epoch=epoch)
        entry.save()
        return entry
