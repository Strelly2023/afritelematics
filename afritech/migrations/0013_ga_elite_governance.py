from __future__ import annotations

import uuid

import django.utils.timezone
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("afritech", "0012_trust_graph_record"),
    ]

    operations = [
        migrations.CreateModel(
            name="GovernanceRule",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(db_index=True, max_length=128, unique=True)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="GovernanceRuleVersion",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("version", models.PositiveIntegerField()),
                ("condition_key", models.CharField(max_length=128)),
                ("expected_value", models.CharField(max_length=128)),
                ("priority", models.CharField(choices=[("critical", "Critical"), ("warning", "Warning")], default="critical", max_length=20)),
                ("description", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("pending", "Pending approval"), ("approved", "Approved"), ("rejected", "Rejected"), ("active", "Active")], default="draft", max_length=20)),
                ("created_by", models.CharField(default="system", max_length=128)),
                ("approved_by", models.CharField(blank=True, max_length=128)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("parent_version", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="afritech.governanceruleversion")),
                ("rule", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="afritech.governancerule")),
            ],
            options={
                "ordering": ["rule__name", "-version"],
                "indexes": [
                    models.Index(fields=["status"], name="afritech_go_status_0cef05_idx"),
                    models.Index(fields=["condition_key"], name="afritech_go_conditi_3fc3ee_idx"),
                    models.Index(fields=["created_at"], name="afritech_go_created_7cb2d2_idx"),
                ],
                "unique_together": {("rule", "version")},
            },
        ),
        migrations.AddField(
            model_name="governancerule",
            name="active_version",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="afritech.governanceruleversion"),
        ),
        migrations.CreateModel(
            name="GovernanceChangeRequest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("requested_by", models.CharField(default="operator", max_length=128)),
                ("required_approvals", models.PositiveIntegerField(default=2)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=20)),
                ("reviewer", models.CharField(blank=True, max_length=128)),
                ("decision_notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("rule_version", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="afritech.governanceruleversion")),
            ],
            options={
                "ordering": ["-created_at", "id"],
                "indexes": [
                    models.Index(fields=["status"], name="afritech_go_status_29a47b_idx"),
                    models.Index(fields=["created_at"], name="afritech_go_created_339820_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ApprovalVote",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("reviewer", models.CharField(max_length=128)),
                ("vote", models.CharField(choices=[("approve", "Approve"), ("reject", "Reject")], max_length=10)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("change_request", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="afritech.governancechangerequest")),
            ],
            options={
                "ordering": ["created_at", "reviewer"],
                "unique_together": {("change_request", "reviewer")},
            },
        ),
        migrations.CreateModel(
            name="RuleActivationLog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("reason", models.CharField(max_length=128)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("activated_version", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="afritech.governanceruleversion")),
                ("previous_version", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="afritech.governanceruleversion")),
                ("rule", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="afritech.governancerule")),
            ],
            options={
                "ordering": ["-created_at", "id"],
            },
        ),
        migrations.CreateModel(
            name="RuleDependency",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("dependency_type", models.CharField(choices=[("requires", "Requires"), ("conflicts", "Conflicts"), ("influences", "Influences")], max_length=32)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("from_rule", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="outgoing_dependencies", to="afritech.governancerule")),
                ("to_rule", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="incoming_dependencies", to="afritech.governancerule")),
            ],
            options={
                "ordering": ["from_rule__name", "dependency_type", "to_rule__name"],
                "unique_together": {("from_rule", "to_rule", "dependency_type")},
            },
        ),
        migrations.CreateModel(
            name="RiskScore",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("scope", models.CharField(db_index=True, max_length=64)),
                ("reference_id", models.CharField(db_index=True, max_length=128)),
                ("score", models.FloatField()),
                ("level", models.CharField(db_index=True, max_length=20)),
                ("breakdown", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={
                "ordering": ["-created_at", "id"],
                "indexes": [
                    models.Index(fields=["scope", "reference_id"], name="afritech_ri_scope_3e4951_idx"),
                    models.Index(fields=["level"], name="afritech_ri_level_50b6a3_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="PredictionSignal",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("proposal_id", models.CharField(db_index=True, max_length=128)),
                ("predicted_failure", models.BooleanField(db_index=True, default=False)),
                ("confidence", models.FloatField(default=0)),
                ("risk_factors", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={
                "ordering": ["-created_at", "id"],
            },
        ),
        migrations.CreateModel(
            name="ProofCertificate",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("proposal_id", models.CharField(db_index=True, max_length=128, unique=True)),
                ("invariants_proven", models.JSONField(default=list)),
                ("proof_result", models.JSONField(default=dict)),
                ("proof_hash", models.CharField(db_index=True, max_length=128, unique=True)),
                ("status", models.CharField(db_index=True, max_length=20)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={
                "ordering": ["-created_at", "proposal_id"],
            },
        ),
        migrations.CreateModel(
            name="AuditLogExport",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("reference_id", models.CharField(db_index=True, max_length=128)),
                ("data", models.JSONField(default=dict)),
                ("format", models.CharField(default="json", max_length=16)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={
                "ordering": ["-created_at", "reference_id"],
            },
        ),
    ]
