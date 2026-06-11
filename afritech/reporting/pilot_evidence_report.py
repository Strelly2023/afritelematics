from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable


REPORT_CLASSIFICATION = "REVIEWABLE_PILOT_EVIDENCE"
AUTHORITY_SOURCE = "observability_only"
REQUIRED_REVIEW_FIELDS = (
    "pilot_run_id",
    "traceId",
    "driverId",
    "evidenceType",
    "status",
    "durationMs",
    "structuredError",
    "timestamp",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class PilotEvidenceReviewEntry:
    pilot_run_id: str
    traceId: str
    driverId: str
    evidenceType: str
    status: int
    durationMs: int
    structuredError: dict[str, Any] | None
    timestamp: str

    @classmethod
    def from_observability_record(
        cls,
        pilot_run_id: str,
        record: dict[str, Any],
    ) -> "PilotEvidenceReviewEntry":
        return cls(
            pilot_run_id=pilot_run_id,
            traceId=str(record.get("traceId") or "missing"),
            driverId=str(record.get("driverId") or "unknown_driver"),
            evidenceType=str(record.get("evidenceType") or "unknown"),
            status=_int(record.get("status"), default=0),
            durationMs=_int(record.get("durationMs"), default=0),
            structuredError=_structured_error(record.get("structuredError")),
            timestamp=str(record.get("timestamp") or _now()),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "pilot_run_id": self.pilot_run_id,
            "traceId": self.traceId,
            "driverId": self.driverId,
            "evidenceType": self.evidenceType,
            "status": self.status,
            "durationMs": self.durationMs,
            "structuredError": self.structuredError,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class PilotEvidenceRunReport:
    pilot_run_id: str
    entries: tuple[PilotEvidenceReviewEntry, ...] = field(default_factory=tuple)
    generated_at: str = field(default_factory=_now)

    def canonical_dict(self) -> dict[str, Any]:
        entries = [entry.canonical_dict() for entry in self.entries]
        return {
            "classification": REPORT_CLASSIFICATION,
            "production_proof": False,
            "authority_source": AUTHORITY_SOURCE,
            "pilot_run_id": self.pilot_run_id,
            "generated_at": self.generated_at,
            "summary": _summary_metrics(entries),
            "required_review_fields": list(REQUIRED_REVIEW_FIELDS),
            "entries": entries,
        }

    def json_text(self) -> str:
        return json.dumps(self.canonical_dict(), indent=2, sort_keys=True)

    def markdown_text(self) -> str:
        lines = [
            "# Pilot Evidence Run Report",
            "",
            f"- classification: {REPORT_CLASSIFICATION}",
            "- production_proof: false",
            f"- authority_source: {AUTHORITY_SOURCE}",
            f"- pilot_run_id: {self.pilot_run_id}",
            f"- generated_at: {self.generated_at}",
            "",
            "This report is reviewable pilot evidence derived from observability only.",
            "It does not certify production readiness or create proof authority.",
            "",
            "## Summary Metrics",
            "",
        ]
        summary = _summary_metrics([entry.canonical_dict() for entry in self.entries])
        for field in SUMMARY_FIELDS:
            lines.append(f"- {field}: {_markdown_value(summary[field])}")
        lines.extend(
            [
                "",
                "## Evidence Observations",
                "",
            ]
        )
        if not self.entries:
            lines.append("No observability records supplied.")
            return "\n".join(lines) + "\n"

        for index, entry in enumerate(self.entries, start=1):
            data = entry.canonical_dict()
            lines.extend(
                [
                    f"### Observation {index}",
                    "",
                    f"- pilot_run_id: {data['pilot_run_id']}",
                    f"- traceId: {data['traceId']}",
                    f"- driverId: {data['driverId']}",
                    f"- evidenceType: {data['evidenceType']}",
                    f"- status: {data['status']}",
                    f"- durationMs: {data['durationMs']}",
                    f"- structuredError: {_markdown_value(data['structuredError'])}",
                    f"- timestamp: {data['timestamp']}",
                    "",
                ]
            )
        return "\n".join(lines)


SUMMARY_FIELDS = (
    "total_observations",
    "success_count",
    "failure_count",
    "success_rate",
    "average_duration_ms",
    "max_duration_ms",
    "evidence_types_seen",
    "unique_driver_count",
    "unique_trace_count",
)


def _summary_metrics(entries: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(entries)
    success_count = sum(1 for entry in entries if _is_success(entry))
    failure_count = total - success_count
    durations = [_int(entry.get("durationMs"), default=0) for entry in entries]
    evidence_types = sorted({str(entry.get("evidenceType") or "unknown") for entry in entries})
    drivers = {str(entry.get("driverId") or "unknown_driver") for entry in entries}
    traces = {str(entry.get("traceId") or "missing") for entry in entries}
    return {
        "total_observations": total,
        "success_count": success_count,
        "failure_count": failure_count,
        "success_rate": round(success_count / total, 4) if total else 0,
        "average_duration_ms": round(sum(durations) / total, 2) if total else 0,
        "max_duration_ms": max(durations) if durations else 0,
        "evidence_types_seen": evidence_types,
        "unique_driver_count": len(drivers),
        "unique_trace_count": len(traces),
    }


def _is_success(entry: dict[str, Any]) -> bool:
    status = _int(entry.get("status"), default=0)
    return 200 <= status < 400 and entry.get("structuredError") is None


def build_pilot_evidence_run_report(
    pilot_run_id: str,
    observability_records: Iterable[dict[str, Any]],
) -> PilotEvidenceRunReport:
    entries = tuple(
        PilotEvidenceReviewEntry.from_observability_record(pilot_run_id, record)
        for record in observability_records
    )
    return PilotEvidenceRunReport(pilot_run_id=pilot_run_id, entries=entries)


def render_pilot_evidence_run_report_json(
    pilot_run_id: str,
    observability_records: Iterable[dict[str, Any]],
) -> str:
    return build_pilot_evidence_run_report(
        pilot_run_id,
        observability_records,
    ).json_text()


def render_pilot_evidence_run_report_markdown(
    pilot_run_id: str,
    observability_records: Iterable[dict[str, Any]],
) -> str:
    return build_pilot_evidence_run_report(
        pilot_run_id,
        observability_records,
    ).markdown_text()


def _structured_error(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return dict(value)
    return {"type": "unknown", "message": str(value)}


def _markdown_value(value: Any) -> str:
    if value is None:
        return "null"
    return f"`{json.dumps(value, sort_keys=True)}`"


def _int(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
