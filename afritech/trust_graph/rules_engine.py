from __future__ import annotations

from typing import Any

from django.db import OperationalError, ProgrammingError

from afritech.models import GovernanceRule, GovernanceRuleVersion


DEFAULT_RULES = (
    {
        "rule": "ride_must_be_pending",
        "version": 1,
        "condition_key": "status",
        "expected": "accepted",
        "priority": "critical",
        "description": "Ride acceptance must result in accepted state evidence.",
        "applies_to": {"RideAccepted"},
    },
    {
        "rule": "driver_required",
        "version": 1,
        "condition_key": "driver_id",
        "expected": "exists",
        "priority": "critical",
        "description": "Driver-mediated ride changes require a driver identifier.",
        "applies_to": {"RideAccepted", "DriverArrived", "TripStarted", "TripCompleted"},
    },
    {
        "rule": "trip_completion_requires_started",
        "version": 1,
        "condition_key": "status",
        "expected": "completed",
        "priority": "critical",
        "description": "Trip completion must result in completed state evidence.",
        "applies_to": {"TripCompleted"},
    },
)


def evaluate_rules(proposal: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    active_rules = get_active_rules(proposal.get("type", ""))
    results = [_evaluate_rule(rule, proposal) for rule in active_rules]

    critical_fail = any(
        not item["passed"] and item.get("priority") == "critical"
        for item in results
    )
    approved = bool(validation.get("passed")) and not critical_fail
    return {
        "approved": approved,
        "rules": results,
    }


def get_active_rules(event_type: str = "") -> list[dict[str, Any]]:
    try:
        versions = [
            rule.active_version
            for rule in GovernanceRule.objects.select_related("active_version").all()
            if rule.active_version is not None
        ]
        if versions:
            return [_serialize_version(version) for version in versions]
    except (OperationalError, ProgrammingError):
        pass

    return [
        rule
        for rule in DEFAULT_RULES
        if not event_type or event_type in rule.get("applies_to", {event_type})
    ]


def _serialize_version(version: GovernanceRuleVersion) -> dict[str, Any]:
    return {
        "rule": version.rule.name,
        "version": version.version,
        "condition_key": version.condition_key,
        "expected": version.expected_value,
        "priority": version.priority,
        "description": version.description,
    }


def _evaluate_rule(rule: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    change = proposal.get("change") or {}
    actual = change.get(rule["condition_key"])
    expected = rule["expected"]
    passed = actual not in (None, "") if expected == "exists" else str(actual) == str(expected)

    return {
        "rule": rule["rule"],
        "version": rule.get("version", 1),
        "passed": passed,
        "expected": expected,
        "actual": actual,
        "priority": rule.get("priority", "critical"),
        "description": rule.get("description", ""),
    }
