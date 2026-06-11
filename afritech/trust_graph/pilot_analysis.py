from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from statistics import mean
from typing import Any

from django.utils import timezone

from .pipeline import list_trust_graph_records


CORRELATION_WINDOW_SECONDS = 10
DEFAULT_LIMIT = 200
STABILITY_WINDOWS = 3
PRODUCTION_READINESS_PROFILES: dict[str, dict[str, Any]] = {
    "melbourne_airport_controlled_pilot": {
        "description": "Controlled airport-zone pilot with known GPS interference and mobile handoff risk.",
        "min_events": 20,
        "min_events_per_required_type": 3,
        "required_event_types": [
            "driver_location_event",
            "gps_accuracy_event",
            "network_latency_event",
            "route_deviation_event",
            "speed_consistency_event",
        ],
        "avg_latency_ms_lt": 500,
        "gps_loss_rate_lt": 0.10,
        "speed_violation_rate_lt": 0.02,
        "correlated_violation_rate_lt": 0.05,
        "max_validated_proposals": 0,
        "required_stability_classification": "stable_or_insufficient_trend",
    }
}


def pilot_evidence_metrics(limit: int = DEFAULT_LIMIT) -> dict[str, Any]:
    records = _pilot_records(limit)
    events = [_event(record) for record in records]
    violations = [event for event in events if event["verdict"] == "violation"]
    latency_values = [
        _number(event["payload"].get("latency_ms"))
        for event in events
        if event["type"] in {"network_latency_event", "ride_accept_latency"}
    ]
    speed_violations = [
        event for event in violations if event["type"] == "speed_consistency_event"
    ]
    gps_signal_loss = [
        event for event in violations if event["type"] == "gps_signal_loss_event"
    ]

    latency_values = [value for value in latency_values if value is not None]
    counts = Counter(event["type"] for event in events)
    violation_counts = Counter(event["type"] for event in violations)
    correlated = movement_sequence_correlations(events)
    correlated_rate = _rate(len(correlated), len(events))
    stability = stability_window_analysis(events)
    metrics = {
        "avg_latency_ms": round(mean(latency_values), 2) if latency_values else None,
        "gps_loss_rate": _rate(len(gps_signal_loss), len(events)),
        "speed_violation_rate": _rate(len(speed_violations), len(events)),
        "correlated_violation_rate": correlated_rate,
    }
    proposals = anomaly_proposals_from_metrics(
        violation_counts,
        correlated,
        metrics,
        stability,
    )

    return {
        "window": {"records_considered": len(records), "limit": limit},
        "totals": {
            "events": len(events),
            "violations": len(violations),
            "observed": sum(1 for event in events if event["verdict"] == "observed"),
            "passed": sum(1 for event in events if event["verdict"] == "pass"),
        },
        "metrics": metrics,
        "event_counts": dict(counts),
        "violation_counts": dict(violation_counts),
        "correlations": correlated,
        "stability": stability,
        "anomaly_proposals": proposals,
    }


def production_readiness_gate(
    metrics_payload: dict[str, Any] | None = None,
    profile: str = "melbourne_airport_controlled_pilot",
) -> dict[str, Any]:
    thresholds = PRODUCTION_READINESS_PROFILES.get(profile)
    if thresholds is None:
        return {
            "profile": profile,
            "classification": "UNKNOWN_PROFILE",
            "production_claim_authorized": False,
            "production_proven": False,
            "authority": "readiness_assessment_only_not_launch_authorization",
            "blocking_reasons": ["unknown readiness profile"],
            "checks": [],
        }

    payload = metrics_payload or pilot_evidence_metrics(limit=DEFAULT_LIMIT)
    totals = payload.get("totals", {})
    metrics = payload.get("metrics", {})
    event_counts = payload.get("event_counts", {})
    stability = payload.get("stability", {})
    proposals = payload.get("anomaly_proposals", [])
    validated_proposals = [
        proposal
        for proposal in proposals
        if proposal.get("status") == "validated_proposal"
    ]
    checks = [
        _readiness_check(
            "minimum_evidence_volume",
            totals.get("events", 0),
            ">=",
            thresholds["min_events"],
        ),
        _required_event_type_check(
            event_counts,
            thresholds["required_event_types"],
            thresholds["min_events_per_required_type"],
        ),
        _readiness_check(
            "average_network_latency_ms",
            metrics.get("avg_latency_ms"),
            "<",
            thresholds["avg_latency_ms_lt"],
            missing_passes=False,
        ),
        _readiness_check(
            "gps_loss_rate",
            metrics.get("gps_loss_rate"),
            "<",
            thresholds["gps_loss_rate_lt"],
        ),
        _readiness_check(
            "speed_violation_rate",
            metrics.get("speed_violation_rate"),
            "<",
            thresholds["speed_violation_rate_lt"],
        ),
        _readiness_check(
            "correlated_violation_rate",
            metrics.get("correlated_violation_rate"),
            "<",
            thresholds["correlated_violation_rate_lt"],
        ),
        _readiness_check(
            "validated_adaptive_proposals",
            len(validated_proposals),
            "<=",
            thresholds["max_validated_proposals"],
        ),
        _readiness_check(
            "time_window_stability",
            stability.get("classification"),
            "==",
            thresholds["required_stability_classification"],
        ),
    ]
    blocking_reasons = [
        check["reason"]
        for check in checks
        if not check["passed"]
    ]
    insufficient_evidence = not checks[0]["passed"]
    threshold_passed = not blocking_reasons
    classification = "PRODUCTION_CANDIDATE_ELIGIBLE"
    if insufficient_evidence:
        classification = "CONTROLLED_PILOT_EVIDENCE_INSUFFICIENT"
    elif not threshold_passed:
        classification = "CONTROLLED_PILOT_CONTINUE"

    return {
        "profile": profile,
        "description": thresholds["description"],
        "classification": classification,
        "production_claim_authorized": threshold_passed,
        "production_proven": False,
        "authority": "readiness_assessment_only_not_launch_authorization",
        "blocking_reasons": blocking_reasons,
        "checks": checks,
        "thresholds": thresholds,
        "observed": {
            "events": totals.get("events", 0),
            "violations": totals.get("violations", 0),
            "validated_proposals": len(validated_proposals),
            "stability_classification": stability.get("classification"),
            "metrics": metrics,
            "event_counts": event_counts,
        },
    }


def movement_sequence_correlations(
    events: list[dict[str, Any]],
    within_seconds: int = CORRELATION_WINDOW_SECONDS,
) -> list[dict[str, Any]]:
    ordered = sorted(
        [event for event in events if event["timestamp"] is not None],
        key=lambda event: event["timestamp"],
    )
    correlations: list[dict[str, Any]] = []
    for index, event in enumerate(ordered):
        if event["type"] != "gps_signal_loss_event" or event["verdict"] != "violation":
            continue
        window_end = event["timestamp"] + timedelta(seconds=within_seconds)
        for candidate in ordered[index + 1 :]:
            if candidate["timestamp"] > window_end:
                break
            if candidate["type"] in {"route_deviation_event", "speed_consistency_event"}:
                correlations.append(
                    {
                        "pattern": "gps_loss_followed_by_movement_violation",
                        "first_event": event["type"],
                        "second_event": candidate["type"],
                        "driver_id": event["driver_id"],
                        "within_seconds": within_seconds,
                        "first_recorded_at": event["timestamp"].isoformat(),
                        "second_recorded_at": candidate["timestamp"].isoformat(),
                        "classification": "correlated_violation",
                    }
                )
    return correlations


def anomaly_proposals_from_metrics(
    violation_counts: Counter[str],
    correlations: list[dict[str, Any]],
    metrics: dict[str, Any],
    stability: dict[str, Any],
) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    if violation_counts.get("network_latency_event", 0) >= 3:
        proposals.append(
            _proposal(
                "network_latency_degradation",
                "Investigate network handoff or backend latency during pilot route.",
                "pilot_latency_threshold_validator",
                metrics,
                stability,
            )
        )
    if violation_counts.get("gps_signal_loss_event", 0) >= 2:
        proposals.append(
            _proposal(
                "gps_signal_instability",
                "Add route-zone fallback handling for GPS loss segments.",
                "real_device_validator.gps_signal_loss",
                metrics,
                stability,
            )
        )
    if correlations:
        proposals.append(
            _proposal(
                "movement_sequence_correlation",
                "Correlated GPS loss and movement violations require pilot route review.",
                "movement_sequence_validator",
                metrics,
                stability,
            )
        )
    if stability["classification"] == "system_degradation":
        proposals.append(
            _proposal(
                "stability_window_degradation",
                "Pause pilot expansion and inspect degradation trend across windows.",
                "time_window_stability_validator",
                metrics,
                stability,
            )
        )
    return sorted(
        proposals,
        key=lambda proposal: proposal["priority_score"],
        reverse=True,
    )


def stability_window_analysis(
    events: list[dict[str, Any]],
    windows: int = STABILITY_WINDOWS,
) -> dict[str, Any]:
    ordered = sorted(
        [event for event in events if event["timestamp"] is not None],
        key=lambda event: event["timestamp"],
    )
    if not ordered:
        return {
            "validator": "time_window_stability_validator",
            "classification": "insufficient_evidence",
            "windows": [],
            "increasing_violation_rate": False,
        }

    window_size = max(len(ordered) // windows, 1)
    chunks = [
        ordered[index : index + window_size]
        for index in range(0, len(ordered), window_size)
    ][-windows:]
    summarized = []
    for index, chunk in enumerate(chunks, start=1):
        violations = [event for event in chunk if event["verdict"] == "violation"]
        summarized.append(
            {
                "window": index,
                "events": len(chunk),
                "violations": len(violations),
                "violation_rate": _rate(len(violations), len(chunk)),
                "start": chunk[0]["timestamp"].isoformat(),
                "end": chunk[-1]["timestamp"].isoformat(),
            }
        )

    rates = [window["violation_rate"] for window in summarized]
    increasing = len(rates) >= 3 and all(
        earlier < later for earlier, later in zip(rates, rates[1:])
    )
    return {
        "validator": "time_window_stability_validator",
        "classification": "system_degradation" if increasing else "stable_or_insufficient_trend",
        "windows": summarized,
        "increasing_violation_rate": increasing,
    }


def validate_anomaly_proposal(
    proposal: dict[str, Any],
    metrics: dict[str, Any],
    stability: dict[str, Any],
) -> dict[str, Any]:
    anomaly_type = proposal["anomaly_type"]
    requirements = {
        "network_latency_degradation": [
            {
                "metric": "avg_latency_ms",
                "operator": ">=",
                "threshold": 800,
                "actual": metrics.get("avg_latency_ms"),
            }
        ],
        "gps_signal_instability": [
            {
                "metric": "gps_loss_rate",
                "operator": ">=",
                "threshold": 0.15,
                "actual": metrics.get("gps_loss_rate"),
            }
        ],
        "movement_sequence_correlation": [
            {
                "metric": "correlated_violation_rate",
                "operator": ">",
                "threshold": 0,
                "actual": metrics.get("correlated_violation_rate"),
            }
        ],
        "stability_window_degradation": [
            {
                "metric": "increasing_violation_rate",
                "operator": "is",
                "threshold": True,
                "actual": stability.get("increasing_violation_rate"),
            }
        ],
    }.get(anomaly_type, [])
    passed = [_requirement_passes(requirement) for requirement in requirements]
    return {
        "status": "validated_proposal" if requirements and all(passed) else "candidate_proposal",
        "requirements": requirements,
    }


def _requirement_passes(requirement: dict[str, Any]) -> bool:
    actual = requirement.get("actual")
    threshold = requirement.get("threshold")
    operator = requirement.get("operator")
    if operator == ">=":
        return actual is not None and actual >= threshold
    if operator == ">":
        return actual is not None and actual > threshold
    if operator == "is":
        return actual is threshold
    return False


def _priority_score(
    anomaly_type: str,
    metrics: dict[str, Any],
    stability: dict[str, Any],
) -> int:
    score = 10
    if anomaly_type == "movement_sequence_correlation":
        score += int((metrics.get("correlated_violation_rate") or 0) * 100)
    if anomaly_type == "gps_signal_instability":
        score += int((metrics.get("gps_loss_rate") or 0) * 100)
    if anomaly_type == "network_latency_degradation":
        avg_latency = metrics.get("avg_latency_ms") or 0
        score += min(int(avg_latency / 100), 30)
    if stability.get("classification") == "system_degradation":
        score += 40
    return score


def _readiness_check(
    name: str,
    actual: Any,
    operator: str,
    threshold: Any,
    missing_passes: bool = True,
) -> dict[str, Any]:
    passed = _comparison_passes(actual, operator, threshold, missing_passes)
    return {
        "name": name,
        "operator": operator,
        "threshold": threshold,
        "actual": actual,
        "passed": passed,
        "reason": (
            f"{name} {actual!r} must be {operator} {threshold!r}"
            if not passed
            else ""
        ),
    }


def _required_event_type_check(
    event_counts: dict[str, int],
    required_event_types: list[str],
    minimum_count: int,
) -> dict[str, Any]:
    observed = {
        event_type: int(event_counts.get(event_type, 0))
        for event_type in required_event_types
    }
    missing = [
        event_type
        for event_type, count in observed.items()
        if count < minimum_count
    ]
    passed = not missing
    return {
        "name": "minimum_evidence_per_required_type",
        "operator": ">=",
        "threshold": minimum_count,
        "actual": observed,
        "required_event_types": required_event_types,
        "passed": passed,
        "reason": (
            f"minimum_evidence_per_required_type missing {missing}; "
            f"each required type must be >= {minimum_count}"
            if not passed
            else ""
        ),
    }


def _comparison_passes(
    actual: Any,
    operator: str,
    threshold: Any,
    missing_passes: bool,
) -> bool:
    if actual is None:
        return missing_passes
    if operator == "<":
        return actual < threshold
    if operator == "<=":
        return actual <= threshold
    if operator == ">=":
        return actual >= threshold
    if operator == "==":
        return actual == threshold
    return False


def _pilot_records(limit: int) -> list[dict[str, Any]]:
    return [
        record
        for record in list_trust_graph_records(limit=limit)
        if record.get("proposal", {}).get("type") == "PilotEvidenceCaptured"
    ]


def _event(record: dict[str, Any]) -> dict[str, Any]:
    change = record.get("proposal", {}).get("change", {})
    payload = change.get("payload") if isinstance(change.get("payload"), dict) else {}
    validator = change.get("validator") if isinstance(change.get("validator"), dict) else {}
    return {
        "type": change.get("type"),
        "driver_id": change.get("driver_id"),
        "payload": payload,
        "verdict": change.get("verdict", "observed"),
        "validator": validator,
        "timestamp": _parse_timestamp(change.get("recorded_at") or record.get("created_at")),
    }


def _proposal(
    anomaly_type: str,
    recommendation: str,
    validator: str,
    metrics: dict[str, Any],
    stability: dict[str, Any],
) -> dict[str, Any]:
    proposal = {
        "proposal_type": "pilot_anomaly_response",
        "anomaly_type": anomaly_type,
        "validator": validator,
        "recommendation": recommendation,
        "authority": "proposal_only_not_execution",
        "priority_score": _priority_score(anomaly_type, metrics, stability),
    }
    proposal["validation"] = validate_anomaly_proposal(
        proposal,
        metrics,
        stability,
    )
    proposal["status"] = proposal["validation"]["status"]
    return proposal


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return timezone.make_aware(parsed, timezone=timezone.utc)
    return parsed


def _number(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _rate(count: int, total: int) -> float:
    if total == 0:
        return 0
    return round(count / total, 4)
