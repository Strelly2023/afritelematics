from __future__ import annotations

from typing import Any

from django.db import transaction
from django.utils import timezone

from afritech.models import (
    ApprovalVote,
    GovernanceChangeRequest,
    GovernanceRule,
    GovernanceRuleVersion,
    RuleActivationLog,
)


def create_rule_version(data: dict[str, Any], user: str = "operator") -> GovernanceRuleVersion:
    rule, _ = GovernanceRule.objects.get_or_create(name=data["name"])
    latest = (
        GovernanceRuleVersion.objects.filter(rule=rule).order_by("-version").first()
    )
    return GovernanceRuleVersion.objects.create(
        rule=rule,
        version=latest.version + 1 if latest else 1,
        condition_key=data["condition_key"],
        expected_value=data["expected_value"],
        priority=data.get("priority", "critical"),
        description=data.get("description", ""),
        status=data.get("status", "draft"),
        created_by=user,
        parent_version=latest,
    )


def submit_for_approval(
    version_id: str,
    user: str = "operator",
    required_approvals: int = 2,
) -> GovernanceChangeRequest:
    rule_version = GovernanceRuleVersion.objects.get(id=version_id)
    rule_version.status = "pending"
    rule_version.save(update_fields=["status"])
    return GovernanceChangeRequest.objects.create(
        rule_version=rule_version,
        requested_by=user,
        required_approvals=required_approvals,
    )


@transaction.atomic
def register_vote(request_id: str, reviewer: str, vote: str) -> dict[str, Any]:
    change = GovernanceChangeRequest.objects.select_for_update().get(id=request_id)
    ApprovalVote.objects.update_or_create(
        change_request=change,
        reviewer=reviewer,
        defaults={"vote": vote},
    )
    votes = ApprovalVote.objects.filter(change_request=change)
    approvals = votes.filter(vote="approve").count()
    rejections = votes.filter(vote="reject").count()

    if rejections:
        change.status = "rejected"
        change.reviewer = reviewer
        change.reviewed_at = timezone.now()
        change.save(update_fields=["status", "reviewer", "reviewed_at"])

        version = change.rule_version
        version.status = "rejected"
        version.save(update_fields=["status"])
    elif approvals >= change.required_approvals:
        _activate_version(change.rule_version, reviewer, "approved_by_quorum")
        change.status = "approved"
        change.reviewer = reviewer
        change.reviewed_at = timezone.now()
        change.save(update_fields=["status", "reviewer", "reviewed_at"])

    return {
        "status": change.status,
        "approvals": approvals,
        "rejections": rejections,
        "required_approvals": change.required_approvals,
    }


def rollback_rule(rule_name: str, reason: str = "manual") -> dict[str, Any]:
    rule = GovernanceRule.objects.get(name=rule_name)
    last_log = RuleActivationLog.objects.filter(rule=rule).order_by("-created_at").first()
    if not last_log or not last_log.previous_version:
        return {"status": "no_previous_version"}

    previous = last_log.previous_version
    current = rule.active_version
    rule.active_version = previous
    rule.save(update_fields=["active_version"])

    previous.status = "active"
    previous.save(update_fields=["status"])
    if current:
        current.status = "approved"
        current.save(update_fields=["status"])

    RuleActivationLog.objects.create(
        rule=rule,
        activated_version=previous,
        previous_version=current,
        reason=reason,
    )
    return {"status": "rolled_back", "active_version": previous.version}


def _activate_version(
    rule_version: GovernanceRuleVersion,
    reviewer: str,
    reason: str,
) -> None:
    rule = rule_version.rule
    previous = rule.active_version

    if previous and previous.id != rule_version.id:
        previous.status = "approved"
        previous.save(update_fields=["status"])

    rule_version.status = "active"
    rule_version.approved_by = reviewer
    rule_version.approved_at = timezone.now()
    rule_version.save(update_fields=["status", "approved_by", "approved_at"])

    rule.active_version = rule_version
    rule.save(update_fields=["active_version"])

    RuleActivationLog.objects.create(
        rule=rule,
        activated_version=rule_version,
        previous_version=previous,
        reason=reason,
    )
