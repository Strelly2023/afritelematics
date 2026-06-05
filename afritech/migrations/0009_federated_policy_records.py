from __future__ import annotations

import uuid

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("afritech", "0008_federation_models"),
    ]

    operations = [
        migrations.CreateModel(
            name="FederatedPolicyRecord",
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
                ("policy_id", models.CharField(db_index=True, max_length=128)),
                ("version", models.CharField(db_index=True, max_length=64)),
                ("rules", models.JSONField(default=dict)),
                ("issuing_authority", models.CharField(max_length=128)),
                ("signature", models.TextField()),
                ("public_key", models.TextField()),
                ("verified", models.BooleanField(db_index=True, default=False)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "policy_id"],
                "unique_together": {("policy_id", "version")},
            },
        ),
    ]
