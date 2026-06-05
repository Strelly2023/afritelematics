from __future__ import annotations

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("afritech", "0007_persistent_orchestration"),
    ]

    operations = [
        migrations.CreateModel(
            name="FederationNode",
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
                ("region", models.CharField(db_index=True, max_length=128)),
                ("node_type", models.CharField(default="regional", max_length=128)),
                ("public_key", models.TextField()),
                ("endpoint", models.URLField()),
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
                "ordering": ["region", "node_id"],
            },
        ),
        migrations.CreateModel(
            name="CrossNodeEventShare",
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
                ("remote_event_id", models.CharField(db_index=True, max_length=128)),
                ("remote_event_hash", models.CharField(db_index=True, max_length=128)),
                ("remote_bundle_root", models.CharField(db_index=True, max_length=128)),
                ("remote_state_hash", models.CharField(db_index=True, max_length=128)),
                ("signature", models.TextField()),
                ("independently_verified", models.BooleanField(db_index=True, default=False)),
                ("verification_notes", models.TextField(blank=True)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                    ),
                ),
                (
                    "source_node",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="afritech.federationnode",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "id"],
                "unique_together": {("source_node", "remote_event_hash")},
            },
        ),
    ]
