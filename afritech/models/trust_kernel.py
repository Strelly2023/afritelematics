from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class EventRecord(models.Model):
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=128, db_index=True)
    actor_id = models.CharField(max_length=128, db_index=True)
    subject_id = models.CharField(max_length=128, db_index=True)
    prev_hash = models.CharField(max_length=128, blank=True)
    event_hash = models.CharField(max_length=128, unique=True, db_index=True)
    payload = models.JSONField()
    signature = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["created_at", "event_id"]
        indexes = [
            models.Index(fields=["event_type"]),
            models.Index(fields=["actor_id"]),
            models.Index(fields=["subject_id"]),
            models.Index(fields=["created_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            protected = EventRecord.objects.get(pk=self.pk)
            if (
                protected.event_type != self.event_type
                or protected.actor_id != self.actor_id
                or protected.subject_id != self.subject_id
                or protected.prev_hash != self.prev_hash
                or protected.event_hash != self.event_hash
                or protected.payload != self.payload
                or protected.signature != self.signature
            ):
                raise ValueError("IMMUTABLE_EVENT_RECORD_VIOLATION")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"EventRecord<{self.event_type}:{self.event_id}>"


class EvidenceBundle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(EventRecord, on_delete=models.PROTECT)
    receipts = models.JSONField(default=dict)
    witnesses = models.JSONField(default=list)
    bundle_hash = models.CharField(max_length=128, unique=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["created_at", "id"]


class DeviceKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor_id = models.CharField(max_length=128, db_index=True)
    device_id = models.CharField(max_length=128, db_index=True)
    public_key = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        unique_together = ("actor_id", "device_id")
        ordering = ["actor_id", "device_id"]


class WitnessSignature(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(EventRecord, on_delete=models.PROTECT)
    verifier_node = models.CharField(max_length=128, db_index=True)
    signature = models.TextField()
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        unique_together = ("event", "verifier_node")
        ordering = ["created_at", "id"]


class VerifierNode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node_id = models.CharField(max_length=128, unique=True, db_index=True)
    region = models.CharField(max_length=128, blank=True)
    public_key = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["node_id"]

    def __str__(self) -> str:
        return f"VerifierNode<{self.node_id}>"


class ReplaySubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verifier_node = models.ForeignKey(VerifierNode, on_delete=models.PROTECT)
    state_hash = models.CharField(max_length=128, db_index=True)
    replay_window_hash = models.CharField(max_length=128, blank=True, db_index=True)
    event_count = models.PositiveIntegerField(default=0)
    signature = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["state_hash"]),
            models.Index(fields=["created_at"]),
        ]


class ReplayAttestation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(EventRecord, on_delete=models.PROTECT)
    verifier_node = models.ForeignKey(VerifierNode, on_delete=models.PROTECT)
    state_hash = models.CharField(max_length=128, db_index=True)
    replay_window_hash = models.CharField(max_length=128, db_index=True)
    signature = models.TextField()
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        unique_together = ("event", "verifier_node")
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["state_hash"]),
            models.Index(fields=["replay_window_hash"]),
        ]


class LedgerRootLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    root_hash = models.CharField(max_length=128, unique=True, db_index=True)
    event_count = models.PositiveIntegerField(default=0)
    latest_event_hash = models.CharField(max_length=128, blank=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at", "id"]


class PersistentOrchestration(models.Model):
    STATUS_CHOICES = (
        ("CREATED", "Created"),
        ("RUNNING", "Running"),
        ("PARTIAL_PROGRESS", "Partial progress"),
        ("COMPLETED", "Completed"),
        ("PAUSED", "Paused"),
        ("ABORTED", "Aborted"),
        ("FAILED", "Failed"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    orchestration_id = models.CharField(max_length=128, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="CREATED")
    final_state_hash = models.CharField(max_length=128, blank=True)
    fully_verified = models.BooleanField(default=False)
    policy_context = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    last_updated = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at", "orchestration_id"]


class OrchestrationStepState(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("VERIFIED", "Verified"),
        ("FAILED", "Failed"),
        ("SKIPPED", "Skipped"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    orchestration = models.ForeignKey(PersistentOrchestration, on_delete=models.PROTECT)
    step_id = models.CharField(max_length=128, db_index=True)
    domain = models.CharField(max_length=128, db_index=True)
    operation = models.CharField(max_length=128, db_index=True)
    dependencies = models.JSONField(default=list)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="PENDING")
    event_id = models.UUIDField(null=True, blank=True, db_index=True)
    evidence_bundle_hash = models.CharField(max_length=128, blank=True)
    verified = models.BooleanField(default=False)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    last_updated = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        unique_together = ("orchestration", "step_id")
        ordering = ["created_at", "step_id"]


class OperatorActionLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    orchestration = models.ForeignKey(PersistentOrchestration, on_delete=models.PROTECT)
    operator_id = models.CharField(max_length=128)
    action = models.CharField(max_length=64)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at", "id"]


class FederationNode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node_id = models.CharField(max_length=128, unique=True, db_index=True)
    region = models.CharField(max_length=128, db_index=True)
    node_type = models.CharField(max_length=128, default="regional")
    public_key = models.TextField()
    endpoint = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["region", "node_id"]


class CrossNodeEventShare(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_node = models.ForeignKey(FederationNode, on_delete=models.PROTECT)
    remote_event_id = models.CharField(max_length=128, db_index=True)
    remote_event_hash = models.CharField(max_length=128, db_index=True)
    remote_bundle_root = models.CharField(max_length=128, db_index=True)
    remote_state_hash = models.CharField(max_length=128, db_index=True)
    signature = models.TextField()
    independently_verified = models.BooleanField(default=False, db_index=True)
    verification_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        unique_together = ("source_node", "remote_event_hash")
        ordering = ["-created_at", "id"]


class FederatedPolicyRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy_id = models.CharField(max_length=128, db_index=True)
    version = models.CharField(max_length=64, db_index=True)
    rules = models.JSONField(default=dict)
    issuing_authority = models.CharField(max_length=128)
    signature = models.TextField()
    public_key = models.TextField()
    verified = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        unique_together = ("policy_id", "version")
        ordering = ["-created_at", "policy_id"]


class NodeAnnouncementRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node_id = models.CharField(max_length=128, db_index=True)
    public_key = models.TextField()
    region = models.CharField(max_length=128, db_index=True)
    capabilities = models.JSONField(default=list)
    endpoint = models.URLField()
    governance_version = models.CharField(max_length=64)
    signature = models.TextField()
    verified = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        unique_together = ("node_id", "governance_version")
        ordering = ["region", "node_id"]


class ExternalProofReference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_system = models.CharField(max_length=128, db_index=True)
    transaction_hash = models.CharField(max_length=256, db_index=True)
    proof_type = models.CharField(max_length=128, db_index=True)
    raw_reference = models.JSONField(default=dict)
    independently_verified = models.BooleanField(default=False, db_index=True)
    verification_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        unique_together = ("external_system", "transaction_hash", "proof_type")
        ordering = ["-created_at", "external_system"]


class LegalEvidenceExport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(EventRecord, on_delete=models.PROTECT)
    evidence_bundle = models.ForeignKey(EvidenceBundle, on_delete=models.PROTECT)
    jurisdiction = models.CharField(max_length=128, db_index=True)
    compliance_tags = models.JSONField(default=list)
    export_hash = models.CharField(max_length=128, unique=True, db_index=True)
    replay_state_hash = models.CharField(max_length=128)
    signatures = models.JSONField(default=list)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at", "jurisdiction"]


class NodeReputation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node_id = models.CharField(max_length=128, unique=True, db_index=True)
    valid_attestations = models.PositiveIntegerField(default=0)
    invalid_attestations = models.PositiveIntegerField(default=0)
    signature_failures = models.PositiveIntegerField(default=0)
    replay_failures = models.PositiveIntegerField(default=0)
    conflicting_attestations = models.PositiveIntegerField(default=0)
    voting_weight = models.FloatField(default=1.0)
    is_isolated = models.BooleanField(default=False, db_index=True)
    last_reason = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["node_id"]


class ConsensusIncident(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(EventRecord, null=True, blank=True, on_delete=models.PROTECT)
    incident_type = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=64, db_index=True)
    state_hash_counts = models.JSONField(default=dict)
    affected_nodes = models.JSONField(default=list)
    finality_halted = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at", "id"]


class ReplayDivergenceRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(EventRecord, null=True, blank=True, on_delete=models.PROTECT)
    expected_state_hash = models.CharField(max_length=128, db_index=True)
    observed_state_hash = models.CharField(max_length=128, db_index=True)
    code_version = models.CharField(max_length=128, blank=True)
    event_order_hash = models.CharField(max_length=128, blank=True)
    dependency_fingerprint = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=64, default="REPLAY_DIVERGENCE", db_index=True)
    root_cause = models.CharField(max_length=128, blank=True)
    finality_halted = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at", "id"]
