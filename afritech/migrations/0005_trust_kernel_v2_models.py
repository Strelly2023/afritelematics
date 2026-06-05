from __future__ import annotations

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("afritech", "0004_trust_kernel_models"),
    ]

    operations = [
        migrations.CreateModel(
            name="VerifierNode",
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
                ("node_id", models.CharField(db_index=True, max_length=128, unique=True)),
                ("region", models.CharField(blank=True, max_length=128)),
                ("public_key", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                    ),
                ),
            ],
            options={
                "ordering": ["node_id"],
            },
        ),
        migrations.CreateModel(
            name="ReplaySubmission",
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
                ("state_hash", models.CharField(db_index=True, max_length=128)),
                (
                    "replay_window_hash",
                    models.CharField(blank=True, db_index=True, max_length=128),
                ),
                ("event_count", models.PositiveIntegerField(default=0)),
                ("signature", models.TextField(blank=True)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                    ),
                ),
                (
                    "verifier_node",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="afritech.verifiernode",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "id"],
                "indexes": [
                    models.Index(fields=["state_hash"], name="afritech_re_state__35139c_idx"),
                    models.Index(fields=["created_at"], name="afritech_re_created_80117c_idx"),
                ],
            },
        ),
    ]
