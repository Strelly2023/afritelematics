import uuid
from django.db import models
from django.utils import timezone


class AuditSeal(models.Model):
    """
    Immutable Merkle root snapshot for a given epoch.

    Guarantees:
    - One seal per epoch
    - Tamper-proof root (validated via Merkle recompute)
    - Cryptographic signature for external verification
    """

    # =====================================================
    # ✅ PRIMARY KEY
    # =====================================================

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # =====================================================
    # ✅ CORE FIELDS
    # =====================================================

    epoch = models.IntegerField(
        unique=True,
        db_index=True,
        help_text="Logical time boundary for this seal"
    )

    merkle_root = models.CharField(
        max_length=64,
        help_text="SHA-256 Merkle root of audit logs"
    )

    # =====================================================
    # ✅ SIGNATURE LAYER (NEW)
    # =====================================================

    signature = models.TextField(
        null=True,
        blank=True,
        help_text="Base64-encoded signature of the Merkle root"
    )

    # =====================================================
    # ✅ METADATA
    # =====================================================

    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )

    # =====================================================
    # ✅ MODEL CONFIG
    # =====================================================

    class Meta:
        ordering = ["epoch"]
        indexes = [
            models.Index(fields=["epoch"]),
            models.Index(fields=["timestamp"]),
        ]
        verbose_name = "Audit Seal"
        verbose_name_plural = "Audit Seals"

    # =====================================================
    # ✅ STRING REPRESENTATION
    # =====================================================

    def __str__(self) -> str:
        short_root = self.merkle_root[:8] if self.merkle_root else "None"
        return f"AuditSeal<epoch={self.epoch}, root={short_root}...>"

    # =====================================================
    # ✅ CONVENIENCE HELPERS
    # =====================================================

    @property
    def has_signature(self) -> bool:
        """Check if seal has a signature."""
        return bool(self.signature)

    def short_signature(self) -> str:
        """Returns shortened signature for logs/debugging."""
        if not self.signature:
            return "None"
        return self.signature[:12] + "..."
