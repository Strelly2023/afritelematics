from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from afritech.reporting.pilot_evidence_report import AUTHORITY_SOURCE, REPORT_CLASSIFICATION


TREND_CLASSIFICATION = "REVIEWABLE_PILOT_EVIDENCE_TREND"
SUMMARY_METRICS = (
    "total_observations",
    "success_rate",
    "average_duration_ms",
    "max_duration_ms",
    "failure_count",
    "evidence_types_seen",
    "unique_driver_count",
    "unique_trace_count",
)


class PilotEvidenceTrendComparisonError(ValueError):
    """Raised when trend comparison inputs violate review-only boundaries."""


@dataclass(frozen=True)
class PilotEvidenceTrendComparison:
    reports: tuple[dict[str, Any], ...]

    def canonical_dict(self) -> dict[str, Any]:
        sessions = [_session_summary(report) for report in self.reports]
        return {
            "classification": TREND_CLASSIFICATION,
            "production_proof": False,
            "authority_source": AUTHORITY_SOURCE,
            "sessions_compared": [session["pilot_run_id"] for session in sessions],
            "observation_growth": _metric_deltas(sessions, "total_observations"),
            "success_rate_changes": _metric_deltas(sessions, "success_rate"),
            "latency_changes": {
                "average_duration_ms": _metric_deltas(sessions, "average_duration_ms"),
                "max_duration_ms": _metric_deltas(sessions, "max_duration_ms"),
            },
            "new_error_types": _new_error_types(self.reports),
            "driver_participation_changes": _metric_deltas(
                sessions,
                "unique_driver_count",
            ),
            "sessions": sessions,
        }


def compare_pilot_evidence_reports(
    reports: Iterable[dict[str, Any]],
) -> PilotEvidenceTrendComparison:
    normalized = tuple(reports)
    if not normalized:
        raise PilotEvidenceTrendComparisonError("at least one report is required")
    for index, report in enumerate(normalized):
        _validate_report(index, report)
    return PilotEvidenceTrendComparison(reports=normalized)


def _validate_report(index: int, report: dict[str, Any]) -> None:
    if report.get("classification") != REPORT_CLASSIFICATION:
        raise PilotEvidenceTrendComparisonError(
            f"report {index} classification must be REVIEWABLE_PILOT_EVIDENCE"
        )
    if report.get("production_proof") is not False:
        raise PilotEvidenceTrendComparisonError(
            f"report {index} production_proof must be false"
        )
    if report.get("authority_source") != AUTHORITY_SOURCE:
        raise PilotEvidenceTrendComparisonError(
            f"report {index} authority_source must be observability_only"
        )
    if not str(report.get("pilot_run_id") or "").strip():
        raise PilotEvidenceTrendComparisonError(
            f"report {index} missing pilot_run_id"
        )
    summary = report.get("summary")
    if not isinstance(summary, dict):
        raise PilotEvidenceTrendComparisonError(
            f"report {index} missing summary metrics"
        )
    for metric in SUMMARY_METRICS:
        if metric not in summary:
            raise PilotEvidenceTrendComparisonError(
                f"report {index} missing summary metric: {metric}"
            )


def _session_summary(report: dict[str, Any]) -> dict[str, Any]:
    summary = report["summary"]
    return {
        "pilot_run_id": report["pilot_run_id"],
        "total_observations": _number(summary["total_observations"]),
        "success_rate": _number(summary["success_rate"]),
        "average_duration_ms": _number(summary["average_duration_ms"]),
        "max_duration_ms": _number(summary["max_duration_ms"]),
        "failure_count": _number(summary["failure_count"]),
        "evidence_types_seen": list(summary["evidence_types_seen"]),
        "unique_driver_count": _number(summary["unique_driver_count"]),
        "unique_trace_count": _number(summary["unique_trace_count"]),
    }


def _metric_deltas(sessions: list[dict[str, Any]], metric: str) -> list[dict[str, Any]]:
    deltas: list[dict[str, Any]] = []
    previous: dict[str, Any] | None = None
    for session in sessions:
        value = session[metric]
        deltas.append(
            {
                "pilot_run_id": session["pilot_run_id"],
                "value": value,
                "delta_from_previous": None if previous is None else value - previous[metric],
            }
        )
        previous = session
    return deltas


def _new_error_types(reports: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for report in reports:
        current = _error_types(report)
        results.append(
            {
                "pilot_run_id": report["pilot_run_id"],
                "new_error_types": sorted(current - seen),
            }
        )
        seen.update(current)
    return results


def _error_types(report: dict[str, Any]) -> set[str]:
    error_types: set[str] = set()
    for entry in report.get("entries", []):
        if not isinstance(entry, dict):
            continue
        structured_error = entry.get("structuredError")
        if isinstance(structured_error, dict) and structured_error.get("type"):
            error_types.add(str(structured_error["type"]))
    return error_types


def _number(value: Any) -> float:
    if isinstance(value, bool):
        raise PilotEvidenceTrendComparisonError("boolean is not a numeric metric")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise PilotEvidenceTrendComparisonError("summary metric must be numeric") from exc

