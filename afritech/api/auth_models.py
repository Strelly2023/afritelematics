import uuid
import hashlib
from datetime import timedelta

from django.db import models
from django.utils import timezone


class ApiKey(models.Model):
    """
    Enterprise-grade API Key model.

    Features:
    - Zero plaintext key storage (hash only)
    - Automatic suspension (temporary)
    - Automatic revocation (permanent)
    - Usage tracking
    - Failure tracking (for auto-defense)
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
    # ✅ CLIENT INFO
    # =====================================================

    name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Client name"
    )

    # ✅ HASHED KEY (CRITICAL SECURITY)
    key_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="SHA-256 hash of API key"
    )

    # ✅ visible prefix for logs/debug
    prefix = models.CharField(
        max_length=8,
        help_text="First 8 chars of key"
    )

    # =====================================================
    # ✅ STATUS CONTROL
    # =====================================================

    is_active = models.BooleanField(
        default=True,
        db_index=True
    )

    suspended_until = models.DateTimeField(
        null=True,
        blank=True
    )

    # =====================================================
    # ✅ TIMESTAMPS
    # =====================================================

    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    # =====================================================
    # ✅ USAGE TRACKING
    # =====================================================

    request_count = models.PositiveIntegerField(default=0)

    # =====================================================
    # ✅ FAILURE TRACKING
    # =====================================================

    failure_count = models.PositiveIntegerField(default=0)
    last_failure_at = models.DateTimeField(null=True, blank=True)

    # =====================================================
    # ✅ META CONFIG
    # =====================================================

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["key_hash"]),
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    # =====================================================
    # ✅ HASHING UTILITIES
    # =====================================================

    @staticmethod
    def hash_key(raw_key: str) -> str:
        """
        Hash API key using SHA-256
        """
        return hashlib.sha256(raw_key.encode()).hexdigest()

    # =====================================================
    # ✅ STATUS CHECKS
    # =====================================================

    def is_suspended(self) -> bool:
        """
        Check if key is temporarily suspended
        """
        if self.suspended_until:
            return self.suspended_until > timezone.now()
        return False

    # =====================================================
    # ✅ USAGE METHODS
    # =====================================================

    def mark_used(self):
        """
        Track usage
        """
        self.last_used_at = timezone.now()
        self.request_count += 1
        self.save(update_fields=["last_used_at", "request_count"])

    # =====================================================
    # ✅ FAILURE / DEFENSE METHODS
    # =====================================================

    def record_failure(self):
        """
        Record a failure event and apply auto-defense rules
        """
        now = timezone.now()

        self.failure_count += 1
        self.last_failure_at = now

        # ✅ AUTO SUSPEND (5 failures)
        if self.failure_count >= 5 and self.failure_count < 10:
            self.suspend(minutes=10)

        # ✅ AUTO REVOKE (10 failures)
        elif self.failure_count >= 10:
            self.revoke()

        self.save(update_fields=["failure_count", "last_failure_at"])

    def reset_failures(self):
        """
        Reset failure count after successful usage
        """
        self.failure_count = 0
        self.save(update_fields=["failure_count"])

    # =====================================================
    # ✅ SECURITY ACTIONS
    # =====================================================

    def suspend(self, minutes: int = 10):
        """
        Temporarily suspend API key
        """
        self.suspended_until = timezone.now() + timedelta(minutes=minutes)
        self.save(update_fields=["suspended_until"])

    def revoke(self):
        """
        Permanently disable API key
        """
        self.is_active = False
        self.save(update_fields=["is_active"])

    def activate(self):
        """
        Reactivate API key
        """
        self.is_active = True
        self.suspended_until = None
        self.failure_count = 0
        self.save(update_fields=["is_active", "suspended_until", "failure_count"])

    # =====================================================
    # ✅ DISPLAY / LOGGING HELPERS
    # =====================================================

    @property
    def short_key(self):
        return f"{self.prefix}****"

    def __str__(self):
        status = "active"
        if not self.is_active:
            status = "Revoked"
        elif self.is_suspended():
            status = "Suspended"

        return f"{self.name} ({status})"
