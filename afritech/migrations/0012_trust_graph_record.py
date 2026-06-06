from __future__ import annotations

import uuid

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("afritech", "0011_resilience_hardening"),
    ]

    operations = [
        migrations.CreateModel(
            name="TrustGraphRecord",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("node_id", models.CharField(db_index=True, max_length=128, unique=True)),
                ("event_id", models.CharField(db_index=True, max_length=128)),
                ("proposal_id", models.CharField(db_index=True, max_length=128, unique=True)),
                ("source", models.CharField(db_index=True, max_length=128)),
                ("action", models.CharField(db_index=True, max_length=255)),
                ("actor_id", models.CharField(blank=True, db_index=True, max_length=128)),
                ("subject_id", models.CharField(blank=True, db_index=True, max_length=128)),
                ("request_headers", models.JSONField(default=dict)),
                ("proposal", models.JSONField(default=dict)),
                ("validation", models.JSONField(default=dict)),
                ("decision", models.JSONField(default=dict)),
                ("execution", models.JSONField(default=dict)),
                ("linked_to", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={
                "ordering": ["-created_at", "node_id"],
                "indexes": [
                    models.Index(fields=["event_id"], name="afritech_tr_event__1bd52d_idx"),
                    models.Index(fields=["proposal_id"], name="afritech_tr_proposa_8195f1_idx"),
                    models.Index(fields=["action"], name="afritech_tr_action_fa4955_idx"),
                    models.Index(fields=["created_at"], name="afritech_tr_created_efbff7_idx"),
                ],
            },
        ),
    ]
