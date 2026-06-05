from __future__ import annotations

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("afritech", "0005_trust_kernel_v2_models"),
    ]

    operations = [
        migrations.CreateModel(
            name="LedgerRootLog",
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
                ("root_hash", models.CharField(db_index=True, max_length=128, unique=True)),
                ("event_count", models.PositiveIntegerField(default=0)),
                (
                    "latest_event_hash",
                    models.CharField(blank=True, db_index=True, max_length=128),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "id"],
            },
        ),
        migrations.CreateModel(
            name="ReplayAttestation",
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
                    models.CharField(db_index=True, max_length=128),
                ),
                ("signature", models.TextField()),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="afritech.eventrecord",
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
                    models.Index(fields=["state_hash"], name="afritech_re_state_h_c54288_idx"),
                    models.Index(
                        fields=["replay_window_hash"],
                        name="afritech_re_replay__a9388a_idx",
                    ),
                ],
                "unique_together": {("event", "verifier_node")},
            },
        ),
    ]
