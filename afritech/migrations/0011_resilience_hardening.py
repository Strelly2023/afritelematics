from __future__ import annotations

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("afritech", "0010_discovery_interop_legal"),
    ]

    operations = [
        migrations.CreateModel(
            name="NodeReputation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("node_id", models.CharField(db_index=True, max_length=128, unique=True)),
                ("valid_attestations", models.PositiveIntegerField(default=0)),
                ("invalid_attestations", models.PositiveIntegerField(default=0)),
                ("signature_failures", models.PositiveIntegerField(default=0)),
                ("replay_failures", models.PositiveIntegerField(default=0)),
                ("conflicting_attestations", models.PositiveIntegerField(default=0)),
                ("voting_weight", models.FloatField(default=1.0)),
                ("is_isolated", models.BooleanField(db_index=True, default=False)),
                ("last_reason", models.CharField(blank=True, max_length=255)),
                ("updated_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={
                "ordering": ["node_id"],
            },
        ),
        migrations.CreateModel(
            name="ConsensusIncident",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("incident_type", models.CharField(db_index=True, max_length=64)),
                ("status", models.CharField(db_index=True, max_length=64)),
                ("state_hash_counts", models.JSONField(default=dict)),
                ("affected_nodes", models.JSONField(default=list)),
                ("finality_halted", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                (
                    "event",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="afritech.eventrecord"),
                ),
            ],
            options={
                "ordering": ["-created_at", "id"],
            },
        ),
        migrations.CreateModel(
            name="ReplayDivergenceRecord",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("expected_state_hash", models.CharField(db_index=True, max_length=128)),
                ("observed_state_hash", models.CharField(db_index=True, max_length=128)),
                ("code_version", models.CharField(blank=True, max_length=128)),
                ("event_order_hash", models.CharField(blank=True, max_length=128)),
                ("dependency_fingerprint", models.CharField(blank=True, max_length=128)),
                ("status", models.CharField(db_index=True, default="REPLAY_DIVERGENCE", max_length=64)),
                ("root_cause", models.CharField(blank=True, max_length=128)),
                ("finality_halted", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                (
                    "event",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="afritech.eventrecord"),
                ),
            ],
            options={
                "ordering": ["-created_at", "id"],
            },
        ),
    ]
