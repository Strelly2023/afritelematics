from __future__ import annotations

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("afritech", "0006_trust_kernel_v3_models"),
    ]

    operations = [
        migrations.CreateModel(
            name="PersistentOrchestration",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "orchestration_id",
                    models.CharField(db_index=True, max_length=128, unique=True),
                ),
                ("name", models.CharField(max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("CREATED", "Created"),
                            ("RUNNING", "Running"),
                            ("PARTIAL_PROGRESS", "Partial progress"),
                            ("COMPLETED", "Completed"),
                            ("PAUSED", "Paused"),
                            ("ABORTED", "Aborted"),
                            ("FAILED", "Failed"),
                        ],
                        default="CREATED",
                        max_length=32,
                    ),
                ),
                ("final_state_hash", models.CharField(blank=True, max_length=128)),
                ("fully_verified", models.BooleanField(default=False)),
                ("policy_context", models.JSONField(default=dict)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                    ),
                ),
                (
                    "last_updated",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "orchestration_id"],
            },
        ),
        migrations.CreateModel(
            name="OperatorActionLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("operator_id", models.CharField(max_length=128)),
                ("action", models.CharField(max_length=64)),
                ("reason", models.TextField(blank=True)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                    ),
                ),
                (
                    "orchestration",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="afritech.persistentorchestration",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "id"],
            },
        ),
        migrations.CreateModel(
            name="OrchestrationStepState",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("step_id", models.CharField(db_index=True, max_length=128)),
                ("domain", models.CharField(db_index=True, max_length=128)),
                ("operation", models.CharField(db_index=True, max_length=128)),
                ("dependencies", models.JSONField(default=list)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("RUNNING", "Running"),
                            ("VERIFIED", "Verified"),
                            ("FAILED", "Failed"),
                            ("SKIPPED", "Skipped"),
                        ],
                        default="PENDING",
                        max_length=32,
                    ),
                ),
                ("event_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("evidence_bundle_hash", models.CharField(blank=True, max_length=128)),
                ("verified", models.BooleanField(default=False)),
                ("error", models.TextField(blank=True)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                    ),
                ),
                (
                    "last_updated",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                    ),
                ),
                (
                    "orchestration",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="afritech.persistentorchestration",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at", "step_id"],
                "unique_together": {("orchestration", "step_id")},
            },
        ),
    ]
