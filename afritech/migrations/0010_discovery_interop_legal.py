from __future__ import annotations

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("afritech", "0009_federated_policy_records"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExternalProofReference",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("external_system", models.CharField(db_index=True, max_length=128)),
                ("transaction_hash", models.CharField(db_index=True, max_length=256)),
                ("proof_type", models.CharField(db_index=True, max_length=128)),
                ("raw_reference", models.JSONField(default=dict)),
                ("independently_verified", models.BooleanField(db_index=True, default=False)),
                ("verification_notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={
                "ordering": ["-created_at", "external_system"],
                "unique_together": {("external_system", "transaction_hash", "proof_type")},
            },
        ),
        migrations.CreateModel(
            name="NodeAnnouncementRecord",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("node_id", models.CharField(db_index=True, max_length=128)),
                ("public_key", models.TextField()),
                ("region", models.CharField(db_index=True, max_length=128)),
                ("capabilities", models.JSONField(default=list)),
                ("endpoint", models.URLField()),
                ("governance_version", models.CharField(max_length=64)),
                ("signature", models.TextField()),
                ("verified", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={
                "ordering": ["region", "node_id"],
                "unique_together": {("node_id", "governance_version")},
            },
        ),
        migrations.CreateModel(
            name="LegalEvidenceExport",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("jurisdiction", models.CharField(db_index=True, max_length=128)),
                ("compliance_tags", models.JSONField(default=list)),
                ("export_hash", models.CharField(db_index=True, max_length=128, unique=True)),
                ("replay_state_hash", models.CharField(max_length=128)),
                ("signatures", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                (
                    "event",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="afritech.eventrecord"),
                ),
                (
                    "evidence_bundle",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="afritech.evidencebundle"),
                ),
            ],
            options={
                "ordering": ["-created_at", "jurisdiction"],
            },
        ),
    ]
