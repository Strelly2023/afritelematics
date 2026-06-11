from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.reporting.pilot_evidence_report import (
    AUTHORITY_SOURCE,
    REPORT_CLASSIFICATION,
    REQUIRED_REVIEW_FIELDS,
)


class PilotEvidenceReportValidationError(ValueError):
    """Raised when a pilot evidence report violates review-only boundaries."""


@dataclass(frozen=True)
class PilotEvidenceReportValidationResult:
    valid: bool
    classification: str
    production_proof: bool
    authority_source: str
    entry_count: int


def validate_pilot_evidence_report(
    report: dict[str, Any],
) -> PilotEvidenceReportValidationResult:
    if report.get("classification") != REPORT_CLASSIFICATION:
        raise PilotEvidenceReportValidationError(
            "classification must be REVIEWABLE_PILOT_EVIDENCE"
        )

    if report.get("production_proof") is not False:
        raise PilotEvidenceReportValidationError("production_proof must be false")

    if report.get("authority_source") != AUTHORITY_SOURCE:
        raise PilotEvidenceReportValidationError(
            "authority_source must be observability_only"
        )

    entries = report.get("entries")
    if not isinstance(entries, list):
        raise PilotEvidenceReportValidationError("entries must be a list")

    for index, entry in enumerate(entries):
        _validate_entry(index, entry)

    return PilotEvidenceReportValidationResult(
        valid=True,
        classification=REPORT_CLASSIFICATION,
        production_proof=False,
        authority_source=AUTHORITY_SOURCE,
        entry_count=len(entries),
    )


def _validate_entry(index: int, entry: Any) -> None:
    if not isinstance(entry, dict):
        raise PilotEvidenceReportValidationError(
            f"entry {index} must be an object"
        )

    for field in REQUIRED_REVIEW_FIELDS:
        if field not in entry:
            raise PilotEvidenceReportValidationError(
                f"entry {index} missing required field: {field}"
            )

    if not str(entry.get("traceId") or "").strip():
        raise PilotEvidenceReportValidationError(
            f"entry {index} traceId must be present"
        )

